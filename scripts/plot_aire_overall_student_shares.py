
"""Plot student shares of Aire's monthly allocated CPU and GPU resources."""

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

months = pd.period_range("2025-08", "2026-07", freq="M").astype(str)
labels = pd.to_datetime(months, format="%Y-%m").strftime("%b %y")

students = ["UG", "PGT", "PGR"]
legacy = "Unclassified (legacy)"
categories = students + [legacy]

colours = {
    "UG": "#4C78A8",
    "PGT": "#59A14F",
    "PGR": "#C76B70",
    legacy: "#C49A52",
    "All identified students": "#303030",
}


def monthly_shares(partitions, metric):
    """Percentage of monthly allocation going to each account category."""

    subset = df.loc[df["partition"].isin(partitions)]

    grouped = (
        subset.groupby(["month", "category"])[metric]
        .sum()
        .unstack(fill_value=0)
        .reindex(index=months, fill_value=0)
    )

    totals = grouped.sum(axis=1)

    shares = pd.DataFrame(index=months)

    for category in categories:
        values = grouped.get(
            category,
            pd.Series(0.0, index=months),
        )

        shares[category] = (
            100 * values / totals.where(totals > 0)
        )

    shares["All identified students"] = shares[students].sum(
        axis=1, min_count=1
    )

    return shares


cpu = monthly_shares(["nodes", "himem"], "cpu_hours")
gpu = monthly_shares(["gpu"], "gpu_hours")

fig, axes = plt.subplots(
    1, 2, figsize=(10, 5.5), sharex=True, sharey=True
)

for ax, data, title in zip(
    axes,
    [cpu, gpu],
    [
        "CPU allocation: nodes + himem",
        "GPU allocation: gpu partition",
    ],
):
    for category in categories:
        ax.plot(
            labels,
            data[category],
            label=category,
            color=colours[category],
            linestyle="--" if category == legacy else "-",
            linewidth=1.8,
            marker="o",
            markersize=4,
        )

    ax.plot(
        labels,
        data["All identified students"],
        label="All identified students",
        color=colours["All identified students"],
        linewidth=3,
        marker="s",
        markersize=5,
        zorder=5,
    )

    ax.set_title(title)
    #ax.set_ylabel("Share of monthly allocation (%)")
    ax.set_xlabel("")
    ax.set_ylim(-5, 100)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)

handles, legend_labels = axes[0].get_legend_handles_labels()

fig.legend(
    handles,
    legend_labels,
    loc="lower center",
    ncol=5,
    frameon=False,
    fontsize=9,
)

fig.suptitle(
    "Aire: student share of monthly allocated resources\n"
    "August 2025 – July 2026",
    fontsize=15,
)
axes[0].set_ylabel("Share of monthly allocation (%)")
fig.tight_layout(rect=[0, 0.13, 1, 0.93])

output = TABLES / "aire_overall_student_resource_shares.png"
fig.savefig(output, dpi=200, bbox_inches="tight")
plt.close(fig)

print("Saved:", output)
