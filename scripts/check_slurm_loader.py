
"""Check Slurm loading using aggregate statistics only."""

import argparse
from pathlib import Path

from hpc_student_impact.load_slurm import iter_slurm_jobs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--start", default="2025-08-01")
    parser.add_argument("--end", default="2026-08-01")
    args = parser.parse_args()

    # Smoke test: first non-empty chunk only.
    chunks = iter_slurm_jobs(
        args.path,
        start=args.start,
        end=args.end,
        chunksize=100_000,
    )

    chunk = next(chunks, None)

    if chunk is None:
        print("No matching records found.")
        return

    print("Records in test chunk:", len(chunk))
    print("Submitted in period:",
          int(chunk["submitted_in_period"].sum()))
    print("Ran in period:",
          int(chunk["running_in_period"].sum()))

    print("\nPartitions:")
    print(chunk["Partition"].value_counts(dropna=False))

    print("\nSubmission date range:")
    print(chunk["Submit"].min(), "to", chunk["Submit"].max())


if __name__ == "__main__":
    main()
