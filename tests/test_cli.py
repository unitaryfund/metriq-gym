from datetime import datetime
import pytest
from unittest.mock import MagicMock
from metriq_gym.cli import LIST_JOBS_HEADERS, TIMESTAMP_FORMAT
from metriq_gym.job_manager import JobManager, MetriqGymJob
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
        MetriqGymJob(
            id="1234",
            device_name="ibmq_qasm_simulator",
            provider_name="ibmq",
            job_type="Quantum Volume",
            dispatch_time=datetime.strptime("2021-09-01 12:00:00", TIMESTAMP_FORMAT),
            params={},
            data={},
        ),
        MetriqGymJob(
            id="5678",
            device_name="ionq_simulator",
            provider_name="ionq",
            job_type="Quantum Volume",
            dispatch_time=datetime.strptime("2021-09-02 12:00:00", TIMESTAMP_FORMAT),
            params={},
            data={},
        ),
    ]

    list_jobs(mock_job_manager)

    # Capture the output
    captured = capsys.readouterr()

    # Expected output using tabulate
    table = [
        ["1234", "ibmq", "ibmq_qasm_simulator", "Quantum Volume", "2021-09-01 12:00:00"],
        ["5678", "ionq", "ionq_simulator", "Quantum Volume", "2021-09-02 12:00:00"],
    ]
    expected_output = tabulate(table, headers=LIST_JOBS_HEADERS, tablefmt="grid") + "\n"

    assert captured.out == expected_output


def test_list_jobs_no_jobs(mock_job_manager, capsys):
    """Test listing jobs when no jobs are recorded."""
    # Mock no jobs
    mock_job_manager.get_jobs.return_value = []

    list_jobs(mock_job_manager)

    # Capture the output
    captured = capsys.readouterr()

    # Verify the printed output
    assert captured.out == "No jobs found.\n"
