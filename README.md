# HPC Student Impact

Python tools for analysing student use of Slurm HPC systems, developed for University of Leeds Research Computing.

The analysis covers active accounts, student categories (UG, PGT, PGR), and allocated CPU/GPU hours by month and partition. Results can be exported as CSV, Markdown and editable PowerPoint tables.

## Setup

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run tests:

```bash
PYTHONPATH=src python -m pytest -q
```

## Data

The repository contains code and synthetic tests only. Real Slurm and ServiceNow data are held separately.

The scripts currently use local paths and dates for the initial Aire analysis (August 2025–July 2026)
