
"""Export monthly activity as Markdown and tab-separated text."""

from pathlib import Path

import pandas as pd


TABLES = (
    Path.home()
    / "hpc-student-impact-private/aire/activity_tables"
)

source = TABLES / "monthly_active_accounts_2025_2026.csv"
df = pd.read_csv(source)

table = df[
    ["month", "UG", "PGT", "PGR", "Students", "Total"]
].copy()

table["month"] = pd.to_datetime(
    table["month"], format="%Y-%m"
).dt.strftime("%b %Y")

table.columns = [
    "Month", "UG", "PGT", "PGR",
    "All students", "All accounts",
]

# Markdown table
header = "| " + " | ".join(table.columns) + " |"
separator = "| :--- |" + " ---: |" * (len(table.columns) - 1)

rows = [
    "| " + " | ".join(row) + " |"
    for row in table.astype(str).values.tolist()
]

markdown = "\n".join([
    "# Monthly active Aire accounts: Aug 2025 – Jul 2026",
    "",
    "Distinct accounts submitting jobs each month.",
    "",
    header,
    separator,
    *rows,
    "",
    "Each account is counted once per month. "
    "Monthly counts are not additive.",
    "",
]) + "\n"

md_path = TABLES / "monthly_active_accounts_2025_2026.md"
md_path.write_text(markdown, encoding="utf-8")

# Tab-separated text for Excel and PowerPoint
tsv_path = TABLES / "monthly_active_accounts_2025_2026.tsv"
table.to_csv(tsv_path, sep="\t", index=False)

for path in (md_path, tsv_path):
    path.chmod(0o600)
    print("Created:", path)


# Full table: retain every category from the original CSV.
full = df.copy()

full["month"] = pd.to_datetime(
    full["month"], format="%Y-%m"
).dt.strftime("%b %Y")

full = full.rename(columns={
    "month": "Month",
    "Students": "All students",
    "Total": "All accounts",
})

header = "| " + " | ".join(full.columns) + " |"
separator = "| :--- |" + " ---: |" * (len(full.columns) - 1)

rows = [
    "| " + " | ".join(row) + " |"
    for row in full.astype(str).values.tolist()
]

markdown = "\n".join([
    "# Monthly active Aire accounts: Aug 2025 – Jul 2026",
    "",
    "Distinct accounts submitting jobs each month, by category.",
    "",
    header,
    separator,
    *rows,
    "",
    "Each account is counted once per month. "
    "Monthly counts are not additive.",
    "",
]) + "\n"

full_md = TABLES / "monthly_active_accounts_2025_2026_full.md"
full_md.write_text(markdown, encoding="utf-8")

full_tsv = TABLES / "monthly_active_accounts_2025_2026_full.tsv"
full.to_csv(full_tsv, sep="\t", index=False)

for path in (full_md, full_tsv):
    path.chmod(0o600)
    print("Created:", path)
