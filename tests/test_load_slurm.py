
"""Tests for Slurm loading and date filtering."""

import pandas as pd

from hpc_student_impact.load_slurm import (
    filter_slurm_chunk,
    iter_slurm_jobs,
)


START = "2025-08-01"
END = "2026-08-01"


def sample_jobs():
    """Fictional jobs, including boundary cases."""

    return pd.DataFrame({
        "JobID": [
            "100", "100.batch", "102_7",
            "103", "104", "105", "106",
        ],
        "User": [
            "test_a", "test_a", "test_b",
            "test_c", "test_d", "test_e", "test_f",
        ],
        "Submit": [
            "2025-08-03", "2025-08-03",
            "2025-07-31", "2025-09-01",
            "2025-07-28", "2026-07-31",
            "2026-08-02",
        ],
        "Start": [
            "2025-08-03", "2025-08-03",
            "2025-07-31 23:00", None,
            "2025-07-28", "2026-07-31 23:00",
            "2026-08-02",
        ],
        "End": [
            "2025-08-04", "2025-08-04",
            "2025-08-01 01:00", None,
            "2025-07-29", "2026-08-01 02:00",
            "2026-08-03",
        ],
    })


def test_reporting_period():
    result = filter_slurm_chunk(sample_jobs(), START, END)

    assert set(result["JobID"]) == {
        "100", "102_7", "103", "105"
    }


def test_array_task_preserved():
    result = filter_slurm_chunk(sample_jobs(), START, END)

    assert "102_7" in result["JobID"].tolist()
    assert "100.batch" not in result["JobID"].tolist()


def test_boundary_job():
    result = filter_slurm_chunk(sample_jobs(), START, END)

    job = result.set_index("JobID").loc["102_7"]

    assert not job["submitted_in_period"]
    assert job["running_in_period"]


def test_compressed_file(tmp_path):
    path = tmp_path / "synthetic_jobs.csv.gz"
    sample_jobs().to_csv(path, index=False, compression="gzip")

    chunks = list(
        iter_slurm_jobs(path, START, END, chunksize=2)
    )

    result = pd.concat(chunks, ignore_index=True)

    assert len(result) == 4
