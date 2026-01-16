# Fix for LaTeX Hyperref Warnings

## Problem
Warnings like:
```
Token not allowed in a PDF string (PDFDocEncoding): removing 'math shift'
```

These occur when section titles contain `$...$` math mode.

## The Issue
- `\subsection{Global amplitude statistic $S$ (A2-like)}`
- `\subsection{Leverage diagnostic: top-$K$ masking...}`

Hyperref tries to create PDF bookmarks from these titles, but can't handle math mode.

## Solution: Use \texorpdfstring

Replace math in section titles with:
```latex
\texorpdfstring{LATEX VERSION}{PDF BOOKMARK VERSION}
```

## Examples

### Before (causes warning):
```latex
\subsection{Global amplitude statistic $S$ (A2-like)}
```

### After (no warning):
```latex
\subsection{Global amplitude statistic \texorpdfstring{$S$}{S} (A2-like)}
```

---

### Before:
```latex
\subsection{Leverage diagnostic: top-$K$ masking}
```

### After:
```latex
\subsection{Leverage diagnostic: top-\texorpdfstring{$K$}{K} masking}
```

---

### Before:
```latex
\section{Concentration metric: $\gamma_{20}$}
```

### After:
```latex
\section{Concentration metric: \texorpdfstring{$\gamma_{20}$}{gamma-20}}
```

## Quick Fix Script

Save this as `fix_hyperref.sh` and run it:

```bash
#!/bin/bash
# Fix hyperref warnings by adding texorpdfstring

# Backup first
cp sections.tex sections.tex.backup

# Replace common patterns
sed -i 's/\$S\$/\\texorpdfstring{$S$}{S}/g' sections.tex
sed -i 's/\$K\$/\\texorpdfstring{$K$}{K}/g' sections.tex
sed -i 's/top-\$K\$/top-\\texorpdfstring{$K$}{K}/g' sections.tex

echo "Fixed. Check sections.tex and rebuild."
```

## Alternative: Move Math Out of Titles

Sometimes it's cleaner to reword without math:

### Instead of:
```latex
\subsection{Global amplitude statistic $S$ (A2-like)}
```

### Write:
```latex
\subsection{Global amplitude statistic S (A2-like)}
```
(No math mode needed for single letter)

---

### Instead of:
```latex
\subsection{Leverage diagnostic: top-$K$ masking}
```

### Write:
```latex
\subsection{Leverage diagnostic: top-K masking}
```

## Complete Example

```latex
% Before - causes warnings
\section{Results}
\subsection{Baseline statistic $S_0$}
\subsection{After top-$K$ removal}
\subsection{Concentration at different $N_{\text{side}}$ values}

% After - no warnings
\section{Results}
\subsection{Baseline statistic \texorpdfstring{$S_0$}{S0}}
\subsection{After top-\texorpdfstring{$K$}{K} removal}
\subsection{Concentration at different \texorpdfstring{$N_{\text{side}}$}{Nside} values}
```

## To Find All Problematic Lines

Run this in your paper directory:
```bash
grep -n '\(sub\)*section.*\$' sections.tex main.tex
```

This will show you every section/subsection with math that needs fixing.
