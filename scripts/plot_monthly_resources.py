
"""Plot monthly Aire resource allocations by account category."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


TABLES = (
    Path.home()
    / "hpc-student-impact-private/aire/activity_tables"
)

df = pd.read_csv(
    TABLES / "monthly_resource_usage_2025_2026.csv"
)

# Keep student categories and legacy accounts separate.
# Combine the remaining small categories.
categories = [
    "UG",
    "PGT",
    "PGR",
    "Unclassified (legacy)",
    "Staff",
]

other = "Other / testing / unmatched"

df["plot_category"] = df["category"].where(
    df["category"].isin(categories),
    other,
)

categories.append(other)

colours = {
    "UG": "#4C78A8",
    "PGT": "#59A14F",
    "PGR": "#E15759",
    "Unclassified (legacy)": "#F2B134",
    "Staff": "#9D9D9D",
    other: "#B07AA1",
}

months = pd.period_range(
    "2025-08", "2026-07", freq="M"
).astype(str)

plots = {
    "nodes": ("cpu_hours", "Share of monthly CPU-hours (%)"),
    "himem": ("cpu_hours", "Share of monthly CPU-hours (%)"),
    "gpu": ("gpu_hours", "Share of monthly GPU-hours (%)"),
}

for partition, (metric, ylabel) in plots.items():

    subset = df.loc[df["partition"] == partition]

    monthly = subset.pivot_table(
        index="month",
        columns="plot_category",
        values=metric,
        aggfunc="sum",
        fill_value=0,
    )

    monthly = monthly.reindex(
        index=months,
        columns=categories,
        fill_value=0,
    )

    # Convert each month to percentages of that month's total
    totals = monthly.sum(axis=1)
    monthly_pct = monthly.div(totals.replace(0, pd.NA), axis=0) * 100
    monthly_pct = monthly_pct.fillna(0)

    monthly_pct.index = pd.to_datetime(
        monthly_pct.index, format="%Y-%m"
    ).strftime("%b %y")

    fig, ax = plt.subplots(figsize=(11, 5.5))

    monthly_pct.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=[colours[c] for c in categories],
        width=0.8,
    )

    ax.set_title(
        f"Aire {partition}: monthly resource shares\n"
        "August 2025 – July 2026"
    )
    ax.set_xlabel("")
    ax.set_ylabel(ylabel)

    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    ax.legend(
        title="Account category",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
    )

    plt.tight_layout()

    output = TABLES / f"monthly_{partition}_resource_shares.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    print("Saved:", output)

    plt.close(fig)