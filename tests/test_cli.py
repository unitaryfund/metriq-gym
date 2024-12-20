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


@pytest.mark.parametrize(
    "filter_args,expected_ids,unexpected_ids",
    [
        (
            [],
            ["4f50bc94-deab-4d84-bba2-f82f5ab366ca", "2b60bc94-deab-4d84-bba2-f82f5ab377cc"],
            [],
        ),  # No filter
        (
            ["--filter", "provider", "--value", "IBMQ"],
            ["4f50bc94-deab-4d84-bba2-f82f5ab366ca", "2b60bc94-deab-4d84-bba2-f82f5ab377cc"],
            [],
        ),  # Filter by provider
        (
            ["--filter", "backend", "--value", "ibm_toronto"],
            ["2b60bc94-deab-4d84-bba2-f82f5ab377cc"],
            ["4f50bc94-deab-4d84-bba2-f82f5ab366ca"],
        ),  # Filter by backend
    ],
)
def test_list_jobs_with_filters(
    jobs_file: str, filter_args: list[str], expected_ids: list[str], unexpected_ids: list[str]
):
    """Test `list-jobs` functionality with various filters."""
    result = run(
        ["python", f"{_RUN_SCRIPT}", "list-jobs", "-j", str(jobs_file), *filter_args],
        stdout=PIPE,
        text=True,
    )
    output = result.stdout

    # Check that expected job IDs appear in the output.
    for job_id in expected_ids:
        assert job_id in output

    # Check that unexpected job IDs do not appear in the output.
    for job_id in unexpected_ids:
        assert job_id not in output
