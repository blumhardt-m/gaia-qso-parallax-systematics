#!/usr/bin/env python3
"""
make_map_lorenz.py

Generate Mollweide projection map of QSO parallax residuals for paper.

Usage:
    python3 make_map_lorenz.py --input DATA.parquet --output figures/map_lorenz.pdf

Requirements:
    pip install pandas numpy matplotlib healpy
"""

import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import healpy as hp

def find_analysis_data(base_dir):
    """Try to auto-locate the analysis-ready parquet file."""
    base_path = Path(base_dir)
    
    # Search patterns in order of likelihood
    patterns = [
        "data/processed/**/qso_merged*analysis_ready*.parquet",
        "data/processed/**/*analysis_ready*.parquet",
        "data/processed/**/qso_merged*.parquet",
        "data/**/*analysis_ready*.parquet",
        "data/**/qso_*.parquet",
    ]
    
    for pattern in patterns:
        matches = list(base_path.glob(pattern))
        if matches:
            # Return the largest file (most likely the full dataset)
            return max(matches, key=lambda p: p.stat().st_size)
    
    return None

def create_healpix_map(df, nside=32, statistic='parallax'):
    """
    Create HEALPix map from QSO data.
    
    Parameters:
    -----------
    df : DataFrame
        Must have 'ra', 'dec', and statistic columns
    nside : int
        HEALPix resolution
    statistic : str
        Column to map (e.g., 'parallax', 'parallax_over_error')
    
    Returns:
    --------
    hpx_map : array
        HEALPix map values
    """
    # Check required columns
    required_cols = ['ra', 'dec', statistic]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"ERROR: Missing columns: {missing}")
        print(f"Available columns: {df.columns.tolist()}")
        sys.exit(1)
    
    # Convert RA/Dec to theta/phi (healpy uses colatitude)
    theta = np.radians(90.0 - df['dec'].values)  # colatitude
    phi = np.radians(df['ra'].values)             # longitude
    
    # Get pixel indices
    pix = hp.ang2pix(nside, theta, phi)
    
    # Compute median in each pixel
    npix = hp.nside2npix(nside)
    hpx_map = np.full(npix, hp.UNSEEN)
    
    # Group by pixel and compute median
    df_with_pix = df.copy()
    df_with_pix['healpix'] = pix
    
    pixel_stats = df_with_pix.groupby('healpix')[statistic].median()
    
    for pix_id, value in pixel_stats.items():
        if not np.isnan(value):
            hpx_map[pix_id] = value
    
    return hpx_map

def plot_mollweide_map(hpx_map, nside, output_path, title=None, unit='mas'):
    """
    Create publication-quality Mollweide projection.
    
    Parameters:
    -----------
    hpx_map : array
        HEALPix map
    nside : int
        Resolution
    output_path : str or Path
        Output PDF path
    title : str, optional
        Figure title
    unit : str
        Colorbar unit label
    """
    plt.figure(figsize=(12, 6))
    
    # Compute symmetric color limits around zero
    valid_data = hpx_map[hpx_map != hp.UNSEEN]
    if len(valid_data) == 0:
        print("WARNING: No valid data in map!")
        vmin, vmax = -0.1, 0.1
    else:
        vmax = np.percentile(np.abs(valid_data), 95)
        vmin = -vmax
    
    # Create map
    hp.mollview(
        hpx_map,
        coord='C',  # Celestial coordinates
        title=title or f'QSO Parallax Residuals (NSIDE={nside})',
        cmap='RdBu_r',
        min=vmin,
        max=vmax,
        unit=unit,
        cbar=True,
        hold=False,
        flip='astro',  # RA increases to the left
        nest=False
    )
    
    # Add grid
    hp.graticule(verbose=False)
    
    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved map to: {output_path}")
    print(f"  Valid pixels: {np.sum(hpx_map != hp.UNSEEN)}/{len(hpx_map)}")
    print(f"  Data range: [{vmin:.4f}, {vmax:.4f}] {unit}")

def main():
    parser = argparse.ArgumentParser(description='Generate Mollweide map of QSO parallax')
    parser.add_argument('--input', '-i', type=str,
                        help='Input parquet file (auto-detected if not specified)')
    parser.add_argument('--output', '-o', type=str, default='figures/map_lorenz.pdf',
                        help='Output PDF path (default: figures/map_lorenz.pdf)')
    parser.add_argument('--nside', type=int, default=32,
                        help='HEALPix NSIDE (default: 32)')
    parser.add_argument('--statistic', type=str, default='parallax',
                        help='Column to map (default: parallax)')
    parser.add_argument('--project-root', type=str, 
                        default='~/Documents/Research/gaia-qso-parallax-systematics',
                        help='Project root directory')
    
    args = parser.parse_args()
    
    # Expand paths
    project_root = Path(args.project_root).expanduser()
    
    # Find input file
    if args.input:
        input_path = Path(args.input).expanduser()
        if not input_path.exists():
            print(f"ERROR: Input file not found: {input_path}")
            sys.exit(1)
    else:
        print("Auto-detecting input file...")
        input_path = find_analysis_data(project_root)
        if input_path is None:
            print("ERROR: Could not auto-detect input parquet file.")
            print("\nSearched in:")
            print(f"  {project_root}/data/processed/")
            print(f"  {project_root}/data/")
            print("\nPlease specify --input explicitly.")
            sys.exit(1)
        print(f"  Found: {input_path}")
    
    # Create output directory
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print(f"\nLoading data from: {input_path}")
    try:
        df = pd.read_parquet(input_path)
        print(f"  Loaded {len(df):,} rows")
        print(f"  Columns: {df.columns.tolist()}")
    except Exception as e:
        print(f"ERROR loading parquet: {e}")
        sys.exit(1)
    
    # Check for required columns
    if 'ra' not in df.columns or 'dec' not in df.columns:
        print("\nERROR: Missing 'ra' or 'dec' columns!")
        print("Available columns:", df.columns.tolist())
        sys.exit(1)
    
    if args.statistic not in df.columns:
        print(f"\nERROR: Column '{args.statistic}' not found!")
        print("Available columns:", df.columns.tolist())
        
        # Suggest alternatives
        possible = [c for c in df.columns if 'parallax' in c.lower()]
        if possible:
            print(f"\nDid you mean one of these? {possible}")
        sys.exit(1)
    
    # Apply quality cuts (if not already applied)
    print("\nApplying quality filters...")
    initial_len = len(df)
    
    # Remove nulls in key columns
    df = df.dropna(subset=['ra', 'dec', args.statistic])
    print(f"  After removing nulls: {len(df):,} rows ({100*len(df)/initial_len:.1f}%)")
    
    # Optional: apply RUWE cut if column exists
    if 'ruwe' in df.columns:
        df = df[df['ruwe'] < 1.4]
        print(f"  After RUWE < 1.4: {len(df):,} rows ({100*len(df)/initial_len:.1f}%)")
    
    # Create HEALPix map
    print(f"\nCreating HEALPix map (NSIDE={args.nside})...")
    hpx_map = create_healpix_map(df, nside=args.nside, statistic=args.statistic)
    
    # Plot
    print("\nGenerating Mollweide projection...")
    plot_mollweide_map(
        hpx_map, 
        args.nside, 
        output_path,
        title=f'Gaia DR3 QSO Parallax Residuals (N={len(df):,})',
        unit='mas'
    )
    
    print(f"\n✓ SUCCESS: Map saved to {output_path}")

if __name__ == '__main__':
    main()
