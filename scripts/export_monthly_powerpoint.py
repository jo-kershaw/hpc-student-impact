
"""Export monthly Aire activity as an editable PowerPoint table."""

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

source = TABLES / "monthly_active_accounts_2025_2026.csv"
df = pd.read_csv(source)

df["month"] = pd.to_datetime(
    df["month"], format="%Y-%m"
).dt.strftime("%b %Y")

df = df.rename(columns={
    "month": "Month",
    "Students": "All students",
    "Total": "All accounts",
})

# Create a wide slide for the complete table.
prs = Presentation()
prs.slide_width = Inches(16)
prs.slide_height = Inches(9)

slide = prs.slides.add_slide(prs.slide_layouts[6])

title = slide.shapes.add_textbox(
    Inches(0.5), Inches(0.3), Inches(15), Inches(0.6)
)
p = title.text_frame.paragraphs[0]
p.text = "Aire — monthly active accounts, Aug 2025–Jul 2026"
p.font.size = Pt(25)
p.font.bold = True

columns = list(df.columns)

table = slide.shapes.add_table(
    len(df) + 1,
    len(columns),
    Inches(0.5),
    Inches(1.15),
    Inches(15),
    Inches(6.45),
).table

# Give longer headings more space.
widths = {
    "Month": 1.35,
    "Staff testing": 1.25,
    "Infrastructure/vendor": 1.65,
    "Unclassified (legacy)": 1.7,
    "All students": 1.3,
    "All accounts": 1.3,
}

weights = [widths.get(col, 0.85) for col in columns]
total = sum(weights)

for i, weight in enumerate(weights):
    table.columns[i].width = Inches(15 * weight / total)

table.rows[0].height = Inches(0.8)

for i in range(1, len(df) + 1):
    table.rows[i].height = Inches(0.47)

headings = {
    "Staff testing": "Staff\ntesting",
    "Infrastructure/vendor": "Infrastructure/\nvendor",
    "Unclassified (legacy)": "Unclassified\n(legacy)",
    "All students": "All\nstudents",
    "All accounts": "All\naccounts",
}

for row in range(len(df) + 1):
    for col_index, col in enumerate(columns):
        cell = table.cell(row, col_index)

        if row == 0:
            value = headings.get(col, col)
        else:
            entry = df.iloc[row - 1, col_index]
            value = (
                "" if pd.isna(entry)
                else str(entry if col == "Month" else int(entry))
            )

        cell.text = value
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = Inches(0.04)
        cell.margin_right = Inches(0.04)

        cell.fill.solid()
        if row == 0:
            colour = RGBColor(33, 50, 75)
        elif row % 2 == 0:
            colour = RGBColor(244, 246, 249)
        else:
            colour = RGBColor(255, 255, 255)

        cell.fill.fore_color.rgb = colour

        for paragraph in cell.text_frame.paragraphs:
            paragraph.alignment = (
                PP_ALIGN.LEFT if col_index == 0
                else PP_ALIGN.CENTER
            )

            for run in paragraph.runs:
                run.font.size = Pt(12)
                run.font.bold = (
                    row == 0
                    or col in ("All students", "All accounts")
                )
                run.font.color.rgb = (
                    RGBColor(255, 255, 255) if row == 0
                    else RGBColor(33, 50, 75)
                )

note = slide.shapes.add_textbox(
    Inches(0.5), Inches(8.1), Inches(15), Inches(0.5)
)
p = note.text_frame.paragraphs[0]
p.text = (
    "Distinct submitting accounts per month. "
    "Monthly totals are not additive. "
    "All accounts includes staff, legacy and infrastructure accounts."
)
p.font.size = Pt(12)

output = TABLES / "monthly_active_accounts_2025_2026_full.pptx"
prs.save(output)
output.chmod(0o600)

print("Created:", output)
