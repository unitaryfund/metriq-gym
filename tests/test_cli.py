from typing import Any
import pytest
import json
from subprocess import run, PIPE

_RUN_SCRIPT = "metriq_gym/run.py"


@pytest.fixture
def sample_jobs() -> list[dict[str, Any]]:
    return [
        {
            "id": "4f50bc94-deab-4d84-bba2-f82f5ab366ca",
            "backend": "ibm_strasbourg",
            "job_type": "CLOPS",
            "provider": "IBMQ",
            "qubits": 5,
            "shots": 10,
        },
        {
            "id": "2b60bc94-deab-4d84-bba2-f82f5ab377cc",
            "backend": "ibm_toronto",
            "job_type": "QV",
            "provider": "IBMQ",
            "qubits": 7,
            "shots": 20,
        },
    ]


@pytest.fixture
def jobs_file(tmp_path: str, sample_jobs: list) -> str:
    """Creates a temporary jobs file with the provided sample jobs."""
    jobs_file = tmp_path / ".metriq_gym_jobs.jsonl"
    with open(jobs_file, "w") as f:
        for job in sample_jobs:
            f.write(json.dumps(job) + "\n")
    return jobs_file


def test_list_jobs_basic(jobs_file: str):
    result = run(
        ["python", f"{_RUN_SCRIPT}", "list-jobs", "-j", str(jobs_file)],
        stdout=PIPE,
        text=True,
    )
    output = result.stdout

    # Verify output contains job details
    assert "ibm_strasbourg" in output
    assert "ibm_toronto" in output
    assert "CLOPS" in output
    assert "QV" in output


def test_list_jobs_filter_provider(jobs_file: str):
    from subprocess import run, PIPE

    result = run(
        [
            "python",
            f"{_RUN_SCRIPT}",
            "list-jobs",
            "-j",
            str(jobs_file),
            "--filter",
            "provider",
            "--value",
            "IBMQ",
        ],
        stdout=PIPE,
        text=True,
    )
    output = result.stdout

    # Verify output contains all jobs for provider IBMQ.
    assert "ibm_strasbourg" in output
    assert "ibm_toronto" in output
