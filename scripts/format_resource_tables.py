
"""Export annual Aire resource allocations as CSV, Markdown and PPTX.

CPU allocations on the GPU partition are excluded from
the presentation tables but retained in the source data.
"""

from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


TABLES = (
    Path.home()
    / "hpc-student-impact-private/aire/activity_tables"
)

SOURCE = TABLES / "annual_resource_usage_2025_2026.csv"
PREFIX = TABLES / "annual_resource_by_category_2025_2026"

# Partition and primary resource measure.
PARTITIONS = {
    "nodes": "cpu_hours",
    "himem": "cpu_hours",
    "gpu": "gpu_hours",
    "teachingnodes": "cpu_hours",
}

CATEGORIES = [
    "UG",
    "PGT",
    "PGR",
    "Staff",
    "Unclassified (legacy)",
    "Staff testing",
    "Infrastructure/vendor",
    "Other",
    "Unknown",
]

STUDENTS = {"UG", "PGT", "PGR"}


def make_table(source):
    """Build a category-by-partition resource table."""

    extra = sorted(set(source["category"]) - set(CATEGORIES))
    categories = CATEGORIES + extra

    # Preserve unexpected categories rather than dropping them.
    rows = []

    for category in categories + ["All students", "All accounts"]:
        row = {"Category": category}

        for partition, metric in PARTITIONS.items():
            allocations = (
                source.loc[source["partition"] == partition]
                .groupby("category")[metric]
                .sum()
            )

            total = allocations.sum()

            if category == "All accounts":
                value = total
            elif category == "All students":
                value = allocations.reindex(
                    list(STUDENTS), fill_value=0
                ).sum()
            else:
                value = allocations.get(category, 0.0)

            resource = "GPU-h" if metric == "gpu_hours" else "CPU-h"

            row[f"{partition} {resource}"] = float(value)
            row[f"{partition} %"] = (
                100 * value / total if total else 0.0
            )

        rows.append(row)

    return pd.DataFrame(rows)


def format_value(column, value):
    if column == "Category":
        return str(value)
    if column.endswith("%"):
        return f"{value:.1f}%"
    return f"{value:,.0f}"


def export_markdown(table):
    headers = table.columns.tolist()

    lines = [
        "# Aire resource allocation by account category",
        "",
        "**Reporting period:** August 2025 – July 2026",
        "",
        "| " + " | ".join(headers) + " |",
        "| :--- |" + " ---: |" * (len(headers) - 1),
    ]

    for _, row in table.iterrows():
        values = [
            format_value(col, row[col]) for col in headers
        ]
        lines.append("| " + " | ".join(values) + " |")

    lines += [
        "",
        "Allocated resources, not measured utilisation. "
        "CPU-hours on the GPU partition are excluded.",
        "",
        "Student classifications use available ServiceNow "
        "metadata. Legacy accounts are included in "
        "All accounts but not All students.",
    ]

    output = Path(str(PREFIX) + ".md")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    output.chmod(0o600)
    print("Created:", output)


def export_powerpoint(table):
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)

    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(15), Inches(0.6)
    )
    p = title.text_frame.paragraphs[0]
    p.text = "Aire — annual resource allocation by account category"
    p.font.size = Pt(24)
    p.font.bold = True

    subtitle = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.9), Inches(15), Inches(0.3)
    )
    p = subtitle.text_frame.paragraphs[0]
    p.text = "August 2025 – July 2026"
    p.font.size = Pt(14)

    nrows = len(table) + 1
    ncols = len(table.columns)

    ppt_table = slide.shapes.add_table(
        nrows, ncols,
        Inches(0.5), Inches(1.5),
        Inches(15), Inches(5.8),
    ).table

    ppt_table.columns[0].width = Inches(2.55)

    remaining = (15 - 2.55) / (ncols - 1)
    for col in range(1, ncols):
        ppt_table.columns[col].width = Inches(remaining)

    ppt_table.rows[0].height = Inches(0.65)
    for row in range(1, nrows):
        ppt_table.rows[row].height = Inches(0.42)

    for row_index in range(nrows):
        for col_index, column in enumerate(table.columns):
            cell = ppt_table.cell(row_index, col_index)

            if row_index == 0:
                value = column.replace(" ", "\n", 1)
            else:
                value = format_value(
                    column,
                    table.iloc[row_index - 1][column],
                )

            cell.text = value
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.04)
            cell.margin_right = Inches(0.04)

            cell.fill.solid()
            if row_index == 0:
                colour = RGBColor(33, 50, 75)
            elif row_index % 2 == 0:
                colour = RGBColor(244, 246, 249)
            else:
                colour = RGBColor(255, 255, 255)

            cell.fill.fore_color.rgb = colour

            for paragraph in cell.text_frame.paragraphs:
                paragraph.alignment = (
                    PP_ALIGN.LEFT if col_index == 0
                    else PP_ALIGN.RIGHT
                )

                for run in paragraph.runs:
                    run.font.size = Pt(
                        10 if row_index == 0 else 11
                    )
                    run.font.bold = (
                        row_index == 0
                        or value in ("All students", "All accounts")
                    )
                    run.font.color.rgb = (
                        RGBColor(255, 255, 255)
                        if row_index == 0
                        else RGBColor(33, 50, 75)
                    )

    note = slide.shapes.add_textbox(
        Inches(0.5), Inches(7.85), Inches(15), Inches(0.75)
    )
    p = note.text_frame.paragraphs[0]
    p.text = (
        "Allocated resources, not utilisation. "
        "GPU-partition CPU-hours excluded. "
        "All accounts includes legacy and infrastructure accounts. "
        "Student classification uses available ServiceNow records."
    )
    p.font.size = Pt(11)

    output = Path(str(PREFIX) + ".pptx")
    prs.save(output)
    output.chmod(0o600)
    print("Created:", output)


def main():
    source = pd.read_csv(SOURCE)

    # Show partitions omitted from the headline table.
    other = sorted(set(source["partition"]) - set(PARTITIONS))
    if other:
        print("Other partitions retained in source:", other)

    table = make_table(source)

    csv_path = Path(str(PREFIX) + ".csv")
    table.to_csv(csv_path, index=False)
    csv_path.chmod(0o600)
    print("Created:", csv_path)

    export_markdown(table)
    export_powerpoint(table)

    print("\nIdentified student resource shares:")
    students = table.loc[
        table["Category"] == "All students"
    ].iloc[0]

    for partition in PARTITIONS:
        print(f"  {partition:<15} {students[f'{partition} %']:.1f}%")


if __name__ == "__main__":
    main()
