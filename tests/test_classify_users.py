
"""Tests for ServiceNow user classification."""

import pytest

from hpc_student_impact.classify_users import classify_user


@pytest.mark.parametrize(
    "status, expected",
    [
        ("U/G Year 2", "UG"),
        ("U/G Year 3", "UG"),
        ("U/G Year 4", "UG"),
        ("U/G Year 5", "UG"),
        ("U/G Abroad", "UG"),
        ("Masters Student", "PGT"),
        ("P/G", "PGR"),
        ("Staff", "Staff"),
        ("IT Vendor", "Other"),
        ("Unknown status", "Unknown"),
        ("", "Unknown"),
        (None, "Unknown"),
        ("  p/g  ", "PGR"),
    ],
)
def test_classify_user(status, expected):
    assert classify_user(status) == expected
