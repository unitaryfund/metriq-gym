import pytest
from unittest.mock import MagicMock
from metriq_gym.job_manager import JobManager
from metriq_gym.run import list_jobs
from tabulate import tabulate


@pytest.fixture
def mock_job_manager():
    """Fixture to provide a mocked JobManager."""
    return MagicMock(spec=JobManager)


def test_list_jobs_all(mock_job_manager, capsys):
    """Test listing all jobs without filters."""
    # Mock jobs
    mock_job_manager.get_jobs.return_value = [
        {
            "id": "1234",
            "backend": "qasm_simulator",
            "job_type": "benchmark",
            "provider": "ibmq",
            "qubits": 5,
            "shots": 1024,
        },
        {
            "id": "5678",
            "backend": "ionq_simulator",
            "job_type": "experiment",
            "provider": "ionq",
            "qubits": 3,
            "shots": 512,
        },
    ]

    # Mock arguments
    args = MagicMock(filter=None, value=None)

    # Call the function
    list_jobs(args, mock_job_manager)

    # Capture the output
    captured = capsys.readouterr()

    # Expected output using tabulate
    headers = ["ID", "Backend", "Type", "Provider", "Qubits", "Shots"]
    table = [
        ["1234", "qasm_simulator", "benchmark", "ibmq", 5, 1024],
        ["5678", "ionq_simulator", "experiment", "ionq", 3, 512],
    ]
    expected_output = tabulate(table, headers=headers, tablefmt="grid") + "\n"

    assert captured.out == expected_output


def test_list_jobs_no_jobs(mock_job_manager, capsys):
    """Test listing jobs when no jobs are recorded."""
    # Mock no jobs
    mock_job_manager.get_jobs.return_value = []

    # Mock arguments
    args = MagicMock(filter=None, value=None)

    # Call the function
    list_jobs(args, mock_job_manager)

    # Capture the output
    captured = capsys.readouterr()

    # Verify the printed output
    assert captured.out == "No jobs found.\n"
