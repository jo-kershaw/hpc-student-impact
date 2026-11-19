
"""Classify HPC account holders using ServiceNow status."""

def classify_user(status):
    """Return UG, PGT, PGR, Staff, Other or Unknown."""

    if not isinstance(status, str):
        return "Unknown"

    status = status.strip().casefold()

    if status.startswith("u/g "):
        return "UG"

    if status == "masters student":
        return "PGT"

    if status == "p/g":
        return "PGR"

    if status == "staff":
        return "Staff"

    if status == "it vendor":
        return "Other"

    return "Unknown"
