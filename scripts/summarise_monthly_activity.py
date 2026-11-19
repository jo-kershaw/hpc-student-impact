
"""Summarise monthly Aire activity by account category.

Account-level outputs remain outside the Git repository.
"""

from pathlib import Path

import pandas as pd

from hpc_student_impact.load_slurm import iter_slurm_jobs


HOME = Path.home()
DATA = HOME / "code/hpc-analysis-notebook/data"
PRIVATE = HOME / "hpc-student-impact-private/aire"

ACCOUNT_LISTS = PRIVATE / "account_lists"
ACTIVITY_TABLES = PRIVATE / "activity_tables"

SOURCES = [
    (DATA / "df_full_year_test.csv", "2025-08-01", "2025-10-01"),
    (PRIVATE / "df_all_2025_2026.csv.gz", "2025-10-01", "2026-08-01"),
]

CATEGORIES = [
    "UG", "PGT", "PGR", "Staff", "Other",
    "Staff testing", "Infrastructure/vendor",
    "Unclassified (legacy)", "Unknown",
]


def collect_monthly_users():
    """Collect distinct (month, username) pairs."""

    monthly_users = set()

    for path, start, end in SOURCES:
        print(f"Reading {path.name} ...", flush=True)

        for chunk in iter_slurm_jobs(path, start, end):
            submitted = chunk.loc[
                chunk["submitted_in_period"], ["Submit", "User"]
            ].dropna()

            months = submitted["Submit"].dt.strftime("%Y-%m")
            usernames = (
                submitted["User"]
                .astype("string")
                .str.strip()
                .str.lower()
            )

            monthly_users.update(
                (month, username)
                for month, username in zip(months, usernames)
                if username
            )

    return monthly_users


def main():
    # Use classifications and names from the previous analysis.
    accounts = pd.read_csv(
        ACCOUNT_LISTS / "all_active_accounts_2025_2026.csv",
        dtype="string",
    )

    accounts["username"] = accounts["username"].str.strip().str.lower()

    monthly_users = collect_monthly_users()

    activity = pd.DataFrame(
        sorted(monthly_users),
        columns=["month", "username"],
    )

    # Attach account classifications and available full names.
    metadata = accounts.set_index("username")[["name", "category"]]

    activity = activity.join(
        metadata,
        on="username",
        validate="many_to_one",
    )

    if activity["category"].isna().any():
        raise ValueError("Some active accounts have no classification")

    activity["name"] = activity["name"].fillna("")
    activity = activity.sort_values(
        ["month", "category", "username"]
    )

    # Private account-level file for module matching.
    detail_path = ACCOUNT_LISTS / "monthly_account_activity_2025_2026.csv"
    activity.to_csv(detail_path, index=False)
    detail_path.chmod(0o600)

    # Aggregate counts: each account appears once per month.
    summary = (
        activity.groupby(["month", "category"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=CATEGORIES, fill_value=0)
    )

    months = pd.period_range(
        "2025-08", "2026-07", freq="M"
    ).astype(str)

    summary = summary.reindex(months, fill_value=0)

    summary["Students"] = summary[["UG", "PGT", "PGR"]].sum(axis=1)
    summary["Total"] = summary[CATEGORIES].sum(axis=1)

    summary.index.name = "month"

    summary_path = ACTIVITY_TABLES / "monthly_active_accounts_2025_2026.csv"
    summary.to_csv(summary_path)
    summary_path.chmod(0o600)

    print("\nMonthly distinct active accounts:")
    print(summary[["UG", "PGT", "PGR", "Students", "Total"]].to_string())

    print("\nPrivate files created:")
    print(detail_path)
    print(summary_path)


if __name__ == "__main__":
    main()
