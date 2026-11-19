
"""Tests for Slurm allocated resource calculations."""

import pandas as pd
import pytest

from hpc_student_impact.resource_usage import (
    gpu_count,
    calculate_allocated_hours,
)


def test_gpu_count():
    assert gpu_count("cpu=16,gres/gpu=6,mem=64G") == 6
    assert gpu_count("cpu=8,mem=32G") == 0
    assert gpu_count("gres/gpu:h200=2") == 2
    assert gpu_count("gres/gpu=2,gres/gpu:h200=2") == 2
    assert gpu_count(None) == 0


def test_job_crossing_month_boundary():
    jobs = pd.DataFrame({
        "Start": ["2025-09-30 23:00"],
        "End": ["2025-10-01 02:00"],
        "AllocCPUS": [8],
        "AllocTRES": ["cpu=8,gres/gpu=2"],
    })

    result = calculate_allocated_hours(
        jobs, "2025-10-01", "2025-11-01"
    )

    assert result["cpu_alloc_hours"].iloc[0] == pytest.approx(16)
    assert result["gpu_alloc_hours"].iloc[0] == pytest.approx(4)


def test_cpu_only_job():
    jobs = pd.DataFrame({
        "Start": ["2026-01-10 12:00"],
        "End": ["2026-01-10 13:00"],
        "AllocCPUS": [32],
        "AllocTRES": ["cpu=32,mem=64G"],
    })

    result = calculate_allocated_hours(
        jobs, "2026-01-01", "2026-02-01"
    )

    assert result["cpu_alloc_hours"].iloc[0] == pytest.approx(32)
    assert result["gpu_alloc_hours"].iloc[0] == 0


def test_job_without_start():
    jobs = pd.DataFrame({
        "Start": [None],
        "End": [None],
        "AllocCPUS": [16],
        "AllocTRES": ["cpu=16,gres/gpu=2"],
    })

    result = calculate_allocated_hours(
        jobs, "2026-01-01", "2026-02-01"
    )

    assert not result["valid_interval"].iloc[0]
    assert result["cpu_alloc_hours"].iloc[0] == 0
    assert result["gpu_alloc_hours"].iloc[0] == 0
