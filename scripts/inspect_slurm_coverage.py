
"""Inspect date coverage of Slurm accounting files.

Reads large CSV files in chunks.
Prints aggregate information only, never usernames.
"""

import sys
from collections import Counter
from pathlib import Path

import pandas as pd


def inspect_file(path):
    print(f"\n=== {path.name} ===")

    start_months = Counter()
    end_months = Counter()
    total_jobs = 0

    for chunk in pd.read_csv(
        path,
        usecols=["JobID", "Start", "End"],
        dtype={"JobID": "string"},
        chunksize=200_000,
    ):
        # Exclude job steps such as 12345.batch
        main = chunk[
            ~chunk["JobID"].str.contains(".", regex=False, na=False)
        ]

        total_jobs += len(main)

        for col, counter in [
            ("Start", start_months),
            ("End", end_months),
        ]:
            dates = pd.to_datetime(
                main[col], errors="coerce", format="mixed"
            )

            counts = dates.dt.to_period("M").value_counts()

            for month, count in counts.items():
                counter[str(month)] += int(count)

    print(f"Top-level job records: {total_jobs:,}")

    print("\nJobs by start month:")
    for month, count in sorted(start_months.items()):
        print(f"  {month}: {count:,}")

    print("\nJobs by end month:")
    for month, count in sorted(end_months.items()):
        print(f"  {month}: {count:,}")


if __name__ == "__main__":
    for filename in sys.argv[1:]:
        inspect_file(Path(filename))
