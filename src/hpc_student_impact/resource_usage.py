
"""Calculate allocated CPU-hours and GPU-hours from Slurm records."""

import pandas as pd


def gpu_count(alloc_tres):
    """Extract allocated GPU count from Slurm AllocTRES."""

    if pd.isna(alloc_tres):
        return 0

    resources = {}

    for entry in str(alloc_tres).split(","):
        key, separator, value = entry.partition("=")

        if separator and value.isdigit():
            resources[key.strip()] = int(value)

    # Prefer the total GPU count when supplied.
    if "gres/gpu" in resources:
        return resources["gres/gpu"]

    # Otherwise sum GPU-type-specific allocations.
    return sum(
        value
        for key, value in resources.items()
        if key.startswith("gres/gpu:")
    )


def calculate_allocated_hours(df, start, end):
    """Calculate resource allocations within a reporting window.

    start is inclusive; end is exclusive.

    Jobs spanning boundaries contribute only the time
    that overlaps the reporting window.
    """

    start = pd.Timestamp(start)
    end = pd.Timestamp(end)

    if start >= end:
        raise ValueError("Report end must be after start")

    required = {"Start", "End", "AllocCPUS", "AllocTRES"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    result = df.copy()

    job_start = pd.to_datetime(
        result["Start"], errors="coerce", format="mixed"
    )
    job_end = pd.to_datetime(
        result["End"], errors="coerce", format="mixed"
    )

    result["valid_interval"] = (
        job_start.notna()
        & job_end.notna()
        & (job_end > job_start)
    )

    # Restrict each job to the reporting window.
    overlap_start = job_start.clip(lower=start)
    overlap_end = job_end.clip(upper=end)

    hours = (
        (overlap_end - overlap_start)
        .dt.total_seconds()
        .fillna(0)
        .clip(lower=0)
        / 3600
    )

    cpus = (
        pd.to_numeric(result["AllocCPUS"], errors="coerce")
        .fillna(0)
        .clip(lower=0)
    )

    gpus = result["AllocTRES"].map(gpu_count)

    result["cpu_alloc_hours"] = hours * cpus
    result["gpu_alloc_hours"] = hours * gpus

    return result
