
"""Create Aire reference tables from existing activity summaries.

No individual usernames or personal details in the outputs.
"""

from pathlib import Path

import pandas as pd


ROOT = Path.home() / "hpc-student-impact-private/aire"
SOURCE = ROOT / "activity_tables"
DEST = SOURCE / "reference"

DEST.mkdir(parents=True, exist_ok=True)

MONTHS = pd.period_range(
    "2025-08", "2026-07", freq="M"
).astype(str)

BASE = ["UG", "PGT", "PGR", "Unclassified", "Staff", "Other"]
ORDER = [
    "UG", "PGT", "PGR", "Identified students",
    "Unclassified", "Staff", "Other", "Total",
]


def category_group(category):
    if category in ["UG", "PGT", "PGR", "Staff"]:
        return category
    if category == "Unclassified (legacy)":
        return "Unclassified"
    return "Other"


def add_totals(table):
    table = table.reindex(columns=BASE, fill_value=0).copy()
    table["Identified students"] = table[["UG", "PGT", "PGR"]].sum(axis=1)
    table["Total"] = table[BASE].sum(axis=1)
    return table[ORDER]


def as_percent(table):
    return (
        table.div(table["Total"].replace(0, float("nan")), axis=0)
        .mul(100)
        .fillna(0)
        .round(1)
    )


def save(table, filename, decimals=0):
    path = DEST / filename
    table.to_csv(path, float_format=f"%.{decimals}f")
    path.chmod(0o600)
    print("Created:", path.name)


# ---- Active accounts ----

monthly = pd.read_csv(
    SOURCE / "monthly_active_accounts_2025_2026.csv"
).set_index("month")

accounts = pd.DataFrame(index=MONTHS)

for category in ["UG", "PGT", "PGR", "Staff"]:
    accounts[category] = monthly[category]

accounts["Unclassified"] = monthly["Unclassified (legacy)"]

other_columns = [
    "Staff testing", "Infrastructure/vendor", "Other", "Unknown"
]
accounts["Other"] = monthly[
    [c for c in other_columns if c in monthly.columns]
].sum(axis=1)

accounts = add_totals(accounts)

# Annual figures must use distinct usernames, not summed monthly counts.
people = pd.read_csv(
    ROOT / "account_lists/all_active_accounts_2025_2026.csv",
    dtype="string",
).drop_duplicates("username")

annual_counts = (
    people["category"].map(category_group)
    .value_counts()
    .reindex(BASE, fill_value=0)
)

accounts.loc["Annual (unique)"] = add_totals(
    annual_counts.to_frame().T
).iloc[0]

assert (
    accounts.loc[MONTHS, "Total"].to_numpy()
    == monthly.loc[MONTHS, "Total"].to_numpy()
).all()

save(accounts, "active_accounts_numbers.csv")
save(as_percent(accounts), "active_accounts_percent.csv", 1)


# ---- Allocated resources ----

resources = pd.read_csv(
    SOURCE / "monthly_resource_usage_2025_2026.csv"
)

resources["group"] = resources["category"].map(category_group)

partitions = {
    "nodes": (["nodes"], "cpu_hours", "cpu_hours"),
    "himem": (["himem"], "cpu_hours", "cpu_hours"),
    "teachingnodes": (["teachingnodes"], "cpu_hours", "cpu_hours"),
    "cpu_total": (["nodes", "himem"], "cpu_hours", "cpu_hours"),
    "gpu": (["gpu"], "gpu_hours", "gpu_hours"),
}

for partition, (included, metric, label) in partitions.items():
    subset = resources.loc[resources["partition"].isin(included)]

    table = subset.pivot_table(
        index="month",
        columns="group",
        values=metric,
        aggfunc="sum",
        fill_value=0,
    )

    table = table.reindex(
        index=MONTHS,
        columns=BASE,
        fill_value=0,
    )

    # Resource allocations are additive across months.
    table.loc["Annual"] = table.sum(axis=0)

    table = add_totals(table)

    save(
        table.round(2),
        f"{partition}_{label}.csv",
        2,
    )

    save(
        as_percent(table),
        f"{partition}_percent.csv",
        1,
    )

print("\nReference tables complete.")
