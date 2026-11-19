
"""Summarise distinct Aire users submitting jobs during an academic year.

Uses private Slurm and ServiceNow data without displaying usernames.
"""

from collections import Counter
from pathlib import Path

import pandas as pd

from hpc_student_impact.classify_users import classify_user
from hpc_student_impact.load_slurm import iter_slurm_jobs


HOME = Path.home()

# Private/local data sources
DATA = HOME / "code/hpc-analysis-notebook/data"
PRIVATE = HOME / "hpc-student-impact-private/aire"

OLD_USERS = DATA / "users_dep_fac.csv"
NEW_USERS = DATA / "users_dep_fac_2026.csv"

OLD_JOBS = DATA / "df_full_year_test.csv"
NEW_JOBS = PRIVATE / "df_all_2025_2026.csv.gz"

# Reporting period (end exclusive)
START = "2025-08-01"
SPLIT = "2025-10-01"
END = "2026-08-01"


def normalise_usernames(series):
    """Standardise usernames for matching."""
    return series.astype("string").str.strip().str.lower()


def load_user_categories():
    """Combine ServiceNow snapshots, preferring newer information."""

    categories = {}

    for path in [OLD_USERS, NEW_USERS]:
        df = pd.read_csv(
            path,
            usecols=["u_ad_sam_account", "u_status"],
            dtype="string",
        )

        usernames = normalise_usernames(df["u_ad_sam_account"])
        statuses = df["u_status"].fillna("")

        for username, status in zip(usernames, statuses):
            if pd.isna(username) or not username:
                continue

            category = classify_user(status)

            # Keep an earlier known classification if the
            # newer snapshot has an unrecognised status.
            if category != "Unknown" or username not in categories:
                categories[username] = category

    return categories


def load_active_users():
    """Collect unique usernames from submitted Slurm jobs."""

    active_users = set()

    sources = [
        (OLD_JOBS, START, SPLIT),
        (NEW_JOBS, SPLIT, END),
    ]

    for path, start, end in sources:
        print(f"Reading {path.name} ...", flush=True)

        source_users = set()
        submitted_records = 0

        for chunk in iter_slurm_jobs(path, start, end):
            # Active = submitted a job within the reporting period.
            submitted = chunk.loc[
                chunk["submitted_in_period"], "User"
            ]

            submitted_records += len(submitted)

            usernames = normalise_usernames(submitted)
            source_users.update(usernames.dropna())
            source_users.discard("")

        active_users.update(source_users)

        print(f"  Submitted records: {submitted_records:,}")
        print(f"  Distinct users: {len(source_users):,}")

    return active_users


def main():
    categories = load_user_categories()
    active_users = load_active_users()

    counts = Counter(
        categories.get(username, "Unmatched")
        for username in active_users
    )

    print(f"\nAire: {START} to {END} (end exclusive)")
    print(f"Distinct active users: {len(active_users):,}")
    print(f"ServiceNow usernames in combined snapshots: {len(categories):,}")

    print("\nActive users by category:")
    for category in [
        "UG", "PGT", "PGR", "Staff", "Other",
        "Unknown", "Unmatched",
    ]:
        print(f"  {category:<12} {counts[category]:>6,}")

    students = sum(counts[c] for c in ["UG", "PGT", "PGR"])
    print(f"\nTotal classified active students: {students:,}")

    if active_users:
        print(
            "Classified students as % of all active users: "
            f"{100 * students / len(active_users):.1f}%"
        )


if __name__ == "__main__":
    main()
