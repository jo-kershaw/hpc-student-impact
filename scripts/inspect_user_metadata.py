
"""Inspect and compare ServiceNow HPC user exports.

Prints aggregate statistics only; never prints usernames.
"""

import argparse
from pathlib import Path

import pandas as pd

from hpc_student_impact.classify_users import classify_user


def inspect_file(path):
    df = pd.read_csv(path, dtype={"u_ad_sam_account": "string",
                                  "u_status": "string"})

    print(f"\n=== {path.name} ===")
    print(f"Number of records: {len(df):,}")

    print("\nColumns:")
    for col in df.columns:
        print(
            f"  {col}: "
            f"{df[col].notna().sum():,} populated, "
            f"{df[col].nunique(dropna=True):,} distinct"
        )

    print("\nServiceNow status:")
    print(df["u_status"].value_counts(dropna=False))

    print("\nStudent classification:")
    categories = df["u_status"].map(classify_user)
    print(categories.value_counts(dropna=False))

    if "active" in df.columns:
        print("\nServiceNow active field:")
        print(df["active"].value_counts(dropna=False))

    # Keep usernames internally for comparison, never print them.
    users = (
        df["u_ad_sam_account"]
        .dropna()
        .str.strip()
        .str.lower()
    )
    return set(users[users.ne("")])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("earlier", type=Path)
    parser.add_argument("later", type=Path)
    args = parser.parse_args()

    old_users = inspect_file(args.earlier)
    new_users = inspect_file(args.later)

    print("\n=== Comparison ===")
    print("In both files:", len(old_users & new_users))
    print("Only in earlier file:", len(old_users - new_users))
    print("Only in later file:", len(new_users - old_users))
    print("Distinct users overall:", len(old_users | new_users))


if __name__ == "__main__":
    main()
