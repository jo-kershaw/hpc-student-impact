
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

ACCOUNT_LISTS = PRIVATE / "account_lists"

OLD_USERS = DATA / "users_dep_fac.csv"
NEW_USERS = DATA / "users_dep_fac_2026.csv"

OLD_JOBS = DATA / "df_full_year_test.csv"
NEW_JOBS = ACCOUNT_LISTS / "df_all_2025_2026.csv.gz"

# Reporting period (end exclusive)
START = "2025-08-01"
SPLIT = "2025-10-01"
END = "2026-08-01"

LEGACY_CATEGORY = "Unclassified (legacy)"

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

    # Save unmatched usernames for private manual review.
    unmatched = sorted(active_users - set(categories))

    output = ACCOUNT_LISTS / "unmatched_accounts_2025_2026.csv"

    pd.DataFrame({
        "username": unmatched
    }).to_csv(output, index=False)

    output.chmod(0o600)

    print(f"\nSaved {len(unmatched)} unmatched accounts to:")
    print(output)

    # Apply manually verified classifications from a private file.
    overrides_path = PRIVATE / "account_classification_overrides.csv"
    overrides = pd.read_csv(overrides_path, dtype="string")

    override_categories = dict(zip(
        normalise_usernames(overrides["username"]),
        overrides["category"].str.strip(),
    ))

    counts = Counter(
        override_categories.get(
            username,
            categories.get(username, LEGACY_CATEGORY)
        )
        for username in active_users
    )

    # Read full names from ServiceNow.
    # Prefer the newer snapshot, retaining earlier names
    # when the newer record has no name.
    full_names = {}

    for path in [OLD_USERS, NEW_USERS]:
        people = pd.read_csv(
            path,
            usecols=["u_ad_sam_account", "name"],
            dtype="string",
        )

        usernames = normalise_usernames(
            people["u_ad_sam_account"]
        )

        for username, name in zip(usernames, people["name"]):
            if (
                pd.notna(username)
                and username
                and pd.notna(name)
                and name.strip()
            ):
                full_names[username] = name.strip()

    # One record per active Slurm account.
    records = []

    for username in sorted(active_users):
        category = override_categories.get(
            username,
            categories.get(
                username, LEGACY_CATEGORY
            ),
        )

        records.append({
            "username": username,
            "name": full_names.get(username, ""),
            "category": category,
        })

    accounts = pd.DataFrame(records)

    # Save complete account-level data privately.
    output = ACCOUNT_LISTS / "all_active_accounts_2025_2026.csv"
    accounts.to_csv(output, index=False)
    output.chmod(0o600)

    # Save separate lists for module matching and review.
    separate_lists = {
        "UG": "active_UG_2025_2026.csv",
        "PGT": "active_PGT_2025_2026.csv",
        "PGR": "active_PGR_2025_2026.csv",
        LEGACY_CATEGORY: "active_legacy_2025_2026.csv",
    }

    print("\nPrivate account lists:")
    print(f"  All active accounts: {len(accounts):,}")

    for category, filename in separate_lists.items():
        subset = accounts.loc[accounts["category"] == category]

        output = ACCOUNT_LISTS / filename
        subset.to_csv(output, index=False)
        output.chmod(0o600)

        print(f"  {filename}: {len(subset):,} accounts")


    print(f"\nAire: {START} to {END} (end exclusive)")
    print(f"Distinct active users: {len(active_users):,}")
    print(f"ServiceNow usernames in combined snapshots: {len(categories):,}")

    print("\nActive users by category:")
    for category in [
        "UG", "PGT", "PGR", "Staff", "Other",
        "Staff testing", "Infrastructure/vendor",
        LEGACY_CATEGORY, "Unknown",
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
