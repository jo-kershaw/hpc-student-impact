
"""Summarise allocated Aire resources by month, partition and account.

Account-level data is saved outside the Git repository.
CPU allocations on GPU nodes remain separate from other CPU-hours.
"""

from collections import defaultdict
from pathlib import Path

import pandas as pd

from hpc_student_impact.load_slurm import iter_slurm_jobs
from hpc_student_impact.resource_usage import gpu_count


HOME = Path.home()
DATA = HOME / "code/hpc-analysis-notebook/data"
PRIVATE = HOME / "hpc-student-impact-private/aire"
ACCOUNT_LISTS = PRIVATE / "account_lists"
ACTIVITY_TABLES = PRIVATE / "activity_tables"

SOURCES = [
    (DATA / "df_full_year_test.csv", "2025-08-01", "2025-10-01"),
    (PRIVATE / "df_all_2025_2026.csv.gz", "2025-10-01", "2026-08-01"),
]


def collect_allocations():
    """Accumulate allocated hours by month, user and partition."""

    totals = defaultdict(lambda: [0.0, 0.0])

    for path, source_start, source_end in SOURCES:
        print(f"Reading {path.name} ...", flush=True)

        months = pd.period_range(
            source_start,
            pd.Timestamp(source_end) - pd.Timedelta(days=1),
            freq="M",
        )

        for chunk in iter_slurm_jobs(path, source_start, source_end):
            # Only running jobs contribute allocated hours.
            chunk = chunk.loc[chunk["running_in_period"]].copy()

            valid = (
                chunk["Start"].notna()
                & chunk["End"].notna()
                & (chunk["End"] > chunk["Start"])
            )
            chunk = chunk.loc[valid]

            if chunk.empty:
                continue

            starts = chunk["Start"]
            ends = chunk["End"]

            usernames = (
                chunk["User"].astype("string")
                .str.strip().str.lower().fillna("")
            )
            usernames = usernames.mask(
                usernames.eq(""), "(missing username)"
            )

            partitions = (
                chunk["Partition"].astype("string")
                .str.strip().str.lower().fillna("unspecified")
            )

            cpus = (
                pd.to_numeric(chunk["AllocCPUS"], errors="coerce")
                .fillna(0).clip(lower=0)
            )
            gpus = chunk["AllocTRES"].map(gpu_count)

            for month in months:
                window_start = max(
                    month.start_time, pd.Timestamp(source_start)
                )
                window_end = min(
                    (month + 1).start_time,
                    pd.Timestamp(source_end),
                )

                overlapping = (
                    (starts < window_end)
                    & (ends > window_start)
                )

                if not overlapping.any():
                    continue

                idx = chunk.index[overlapping]

                hours = (
                    ends.loc[idx].clip(upper=window_end)
                    - starts.loc[idx].clip(lower=window_start)
                ).dt.total_seconds() / 3600

                portion = pd.DataFrame({
                    "username": usernames.loc[idx],
                    "partition": partitions.loc[idx],
                    "cpu_hours": hours * cpus.loc[idx],
                    "gpu_hours": hours * gpus.loc[idx],
                })

                grouped = (
                    portion.groupby(
                        ["username", "partition"], as_index=False
                    )[["cpu_hours", "gpu_hours"]]
                    .sum()
                )

                for row in grouped.itertuples(index=False):
                    key = (str(month), row.username, row.partition)
                    totals[key][0] += row.cpu_hours
                    totals[key][1] += row.gpu_hours

    return totals


def save_private_csv(df, filename, folder):
    path = folder / filename
    df.to_csv(path, index=False)
    path.chmod(0o600)
    print("Saved:", path)


def main():
    ACTIVITY_TABLES.mkdir(parents=True, exist_ok=True)

    accounts = pd.read_csv(
        ACCOUNT_LISTS / "all_active_accounts_2025_2026.csv",
        dtype="string",
    )
    accounts["username"] = (
        accounts["username"].str.strip().str.lower()
    )

    totals = collect_allocations()

    detail = pd.DataFrame(
        [
            (month, username, partition, values[0], values[1])
            for (month, username, partition), values in totals.items()
        ],
        columns=[
            "month", "username", "partition",
            "cpu_hours", "gpu_hours",
        ],
    )

    detail = detail.merge(
        accounts[["username", "name", "category"]],
        on="username",
        how="left",
        validate="many_to_one",
    )

    # Flag accounts with resource usage but no submission
    # in the academic-year activity list.
    missing = detail["category"].isna()
    if missing.any():
        print(
            "Accounts absent from activity list:",
            detail.loc[missing, "username"].nunique(),
        )

    detail["category"] = detail["category"].fillna(
        "Unclassified (not in activity list)"
    )
    detail["name"] = detail["name"].fillna("")

    detail = detail.sort_values(
        ["month", "partition", "category", "username"]
    )

    save_private_csv(
        detail,
        "monthly_account_resource_usage_2025_2026.csv",
        ACCOUNT_LISTS,
    )

    monthly = (
        detail.groupby(
            ["month", "partition", "category"],
            as_index=False,
        )[["cpu_hours", "gpu_hours"]]
        .sum()
    )

    annual = (
        monthly.groupby(
            ["partition", "category"],
            as_index=False,
        )[["cpu_hours", "gpu_hours"]]
        .sum()
    )

    save_private_csv(
        monthly,
        "monthly_resource_usage_2025_2026.csv",
        ACTIVITY_TABLES,
    )
    save_private_csv(
        annual,
        "annual_resource_usage_2025_2026.csv",
        ACTIVITY_TABLES,
    )

    # Print the overall allocations, keeping partitions separate.
    print("\nAire allocated resources by partition")
    print("Reporting period: Aug 2025 – Jul 2026\n")

    for partition, group in annual.groupby("partition"):
        students = group["category"].isin(["UG", "PGT", "PGR"])

        total_cpu = group["cpu_hours"].sum()
        total_gpu = group["gpu_hours"].sum()
        student_cpu = group.loc[students, "cpu_hours"].sum()
        student_gpu = group.loc[students, "gpu_hours"].sum()

        print(f"{partition}:")
        print(f"  All CPU-hours:      {total_cpu:,.1f}")
        print(f"  Student CPU-hours:  {student_cpu:,.1f}")

        if total_cpu:
            print(
                f"  Student CPU share:  "
                f"{student_cpu / total_cpu:.1%}"
            )

        if total_gpu:
            print(f"  All GPU-hours:      {total_gpu:,.1f}")
            print(f"  Student GPU-hours:  {student_gpu:,.1f}")
            print(
                f"  Student GPU share:  "
                f"{student_gpu / total_gpu:.1%}"
            )

        print()


if __name__ == "__main__":
    main()
