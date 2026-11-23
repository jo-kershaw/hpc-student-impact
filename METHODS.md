# Methods and limitations

## Reporting period

Aire: 1 August 2025 – 31 July 2026.

Slurm accounting records are combined from two datasets covering August–September 2025 and October 2025–July 2026.

## Active accounts

An account is considered active if it submitted at least one Slurm job during the reporting period.

Monthly figures count distinct accounts per month. Annual figures count distinct accounts across the whole year.

Accounts are classified as UG, PGT, PGR or Staff using available ServiceNow records.

## Resource allocation

- **CPU-hours:** allocated CPUs × elapsed running time.
- **GPU-hours:** allocated GPUs × elapsed running time.
- Jobs crossing month boundaries have their allocations divided between months.
- Slurm job steps are excluded.
- CPU allocations on GPU nodes are kept separate.
- The combined CPU figure includes `nodes` and `himem`; `teachingnodes` is reported separately.
- Percentages use the total recorded allocation for the relevant partition and period.

## Limitations

- Historical HPC account creation and closure dates are unavailable.
- Unclassified accounts are retained separately.
- Allocated hours measure resources assigned to jobs, not actual hardware utilisation.
- The `teachingnodes` partition appeared during the reporting period. Earlier teaching activity may have occurred on `nodes`.

Individual account records and source data are not included in this repository.