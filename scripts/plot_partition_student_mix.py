"""Plot monthly partition shares for UG, PGT, PGR and Unclassified."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

TABLES = (
    Path.home()
    / "hpc-student-impact-private/aire/activity_tables"
)

df = pd.read_csv(TABLES / "monthly_resource_usage_2025_2026.csv")

categories = [
    "UG",
    "PGT",
    "PGR",
    "Unclassified (legacy)",
]

partitions = {
    "nodes": ("cpu_hours", "nodes CPU"),
    "himem": ("cpu_hours", "himem CPU"),
    "gpu": ("gpu_hours", "gpu GPU"),
}

colours = {
    "UG": "#4C78A8",                     # muted blue
    "PGT": "#59A14F",                    # muted green
    "PGR": "#E15759",                    # muted red
    "Unclassified (legacy)": "#F2B134",  # amber
}

linestyles = {
    "UG": "-",
    "PGT": "-",
    "PGR": "-",
    "Unclassified (legacy)": "--",
}

months = pd.period_range("2025-08", "2026-07", freq="M").astype(str)
month_labels = pd.to_datetime(months, format="%Y-%m").strftime("%b %y")

for partition, (metric, label) in partitions.items():
    subset = df.loc[df["partition"] == partition].copy()

    monthly_total = (
        subset.groupby("month")[metric]
        .sum()
        .reindex(months, fill_value=0)
    )

    plot_data = pd.DataFrame(index=months)

    for category in categories:
        category_total = (
            subset.loc[subset["category"] == category]
            .groupby("month")[metric]
            .sum()
            .reindex(months, fill_value=0)
        )

        share = category_total.div(monthly_total.replace(0, pd.NA)) * 100
        plot_data[category] = share.fillna(0)

    # Combined share of UG, PGT and PGR accounts.
    plot_data["All identified students"] = (
        plot_data[["UG", "PGT", "PGR"]].sum(axis=1)
    )

    fig, ax = plt.subplots(figsize=(10, 5.5))

    for category in categories:
        ax.plot(
            month_labels,
            plot_data[category],
            marker="o",
            linewidth=2,
            linestyle=linestyles[category],
            label=category,
            color=colours[category],
        )

    ax.plot(
        month_labels,
        plot_data["All identified students"],
        color="#303030",
        linewidth=3,
        linestyle="-",
        marker="s",
        markersize=5,
        label="All identified students",
        zorder=5,
    )

    ax.set_title(
        f"Aire {label}: monthly share by student type\n"
        "August 2025 – July 2026"
    )
    ax.set_xlabel("")
    ax.set_ylabel("Share of partition allocation (%)")
    ax.set_ylim(bottom=-1)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="Account category")

    plt.tight_layout()

    output = TABLES / f"monthly_{partition}_student_mix.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    print("Saved:", output)

    plt.close(fig)
