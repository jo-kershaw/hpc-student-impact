"""Plot monthly partition shares for UG, PGT and PGR on Aire."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

TABLES = (
    Path.home()
    / "hpc-student-impact-private/aire/activity_tables"
)

df = pd.read_csv(TABLES / "monthly_resource_usage_2025_2026.csv")

# Keep only the three student categories we want to plot
student_types = ["UG", "PGT", "PGR"]

# Leave teachingnodes out for now
partitions = {
    "nodes": ("cpu_hours", "nodes CPU"),
    "himem": ("cpu_hours", "himem CPU"),
    "gpu": ("gpu_hours", "gpu GPU"),
}

# Muted colours
colours = {
    "nodes": "#4C78A8",   # muted blue
    "himem": "#59A14F",   # muted green
    "gpu": "#E15759",     # muted red
}

months = pd.period_range("2025-08", "2026-07", freq="M").astype(str)
month_labels = pd.to_datetime(months, format="%Y-%m").strftime("%b %y")

for student in student_types:
    plot_data = pd.DataFrame(index=months)

    for partition, (metric, _) in partitions.items():
        subset = df.loc[df["partition"] == partition].copy()

        # total monthly allocation on this partition
        monthly_total = (
            subset.groupby("month")[metric]
            .sum()
            .reindex(months, fill_value=0)
        )

        # monthly allocation for this student type on this partition
        student_total = (
            subset.loc[subset["category"] == student]
            .groupby("month")[metric]
            .sum()
            .reindex(months, fill_value=0)
        )

        share = student_total.div(monthly_total.replace(0, pd.NA)) * 100
        plot_data[partition] = share.fillna(0)

    fig, ax = plt.subplots(figsize=(10, 5.5))

    for partition, (_, label) in partitions.items():
        ax.plot(
            month_labels,
            plot_data[partition],
            marker="o",
            linewidth=2,
            label=label,
            color=colours[partition],
        )

    ax.set_title(
        f"Aire: monthly partition shares for {student}\n"
        "August 2025 – July 2026"
    )
    ax.set_xlabel("")
    ax.set_ylabel("Share of partition allocation (%)")
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="Partition")

    plt.tight_layout()

    output = TABLES / f"monthly_{student.lower()}_partition_shares.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    print("Saved:", output)

    plt.close(fig)
