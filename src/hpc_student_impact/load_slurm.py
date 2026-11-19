
"""Load and filter Slurm accounting data.

Supports large CSV and CSV.gz files.
Preserves usernames in memory for local analysis.
"""

from pathlib import Path

import pandas as pd


SLURM_COLUMNS = {
    "JobID", "JobIDRaw", "User", "Partition", "State",
    "Submit", "Start", "End",
    "ElapsedRaw", "CPUTimeRAW", "AllocCPUS", "AllocTRES",
}

REQUIRED_COLUMNS = {"JobID", "User", "Submit", "Start", "End"}


def filter_slurm_chunk(df, start, end):
    """Select jobs relevant to the reporting period.

    start is inclusive; end is exclusive.

    Includes jobs submitted within the period or
    whose running intervals overlap the period.
    """

    start = pd.Timestamp(start)
    end = pd.Timestamp(end)

    if start >= end:
        raise ValueError("Report end must be after start")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing Slurm columns: {sorted(missing)}")

    df = df.copy()

    # Remove job steps, but retain array tasks.
    ids = df["JobID"].astype("string")
    main_jobs = ids.notna() & ~ids.str.contains(
        ".", regex=False, na=False
    )

    df = df.loc[main_jobs].copy()

    # Parse timestamps.
    for col in ["Submit", "Start", "End"]:
        df[col] = pd.to_datetime(
            df[col], errors="coerce", format="mixed"
        )

    # Submitted during reporting period.
    submitted = (
        (df["Submit"] >= start)
        & (df["Submit"] < end)
    )

    # Ran at least partly during reporting period.
    running = (
        (df["Start"] < end)
        & (df["End"] > start)
        & (df["End"] > df["Start"])
    )

    keep = submitted | running

    df = df.loc[keep].copy()

    df["submitted_in_period"] = submitted.loc[keep]
    df["running_in_period"] = running.loc[keep]

    return df


def iter_slurm_jobs(path, start, end, chunksize=100_000):
    """Yield relevant Slurm jobs in manageable chunks."""

    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(path)

    for chunk in pd.read_csv(
        path,
        usecols=lambda col: col in SLURM_COLUMNS,
        dtype={"JobID": "string", "User": "string"},
        chunksize=chunksize,
    ):
        filtered = filter_slurm_chunk(chunk, start, end)

        if not filtered.empty:
            yield filtered
