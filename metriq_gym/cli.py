"""Command-line parsing for running metriq benchmarks."""

import argparse

from tabulate import tabulate

from metriq_gym.job_manager import JobManager, MetriqGymJob
from metriq_gym.provider import ProviderType

LIST_JOBS_HEADERS = ["ID", "Provider", "Device", "Type", "Dispatch time (UTC)"]
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def list_jobs(args: argparse.Namespace, job_manager: JobManager) -> int:
    """List jobs recorded in the job manager.

    Args:
        args: Parsed arguments.
        job_manager: Job manager instance.
    Returns:
        Return code.
    """
    # Retrieve all jobs from JobManager.
    jobs: list[MetriqGymJob] = job_manager.get_jobs()

    # Display jobs in a tabular format.
    if not jobs:
        print("No jobs found.")
        return 0

    # Prepare data for tabulation.
    table = [
        [
            job.id,
            job.provider_name,
            job.device_name,
            job.job_type,
            job.dispatch_time.strftime(TIMESTAMP_FORMAT),
        ]
        for job in jobs
    ]
    # Print the table.
    print(tabulate(table, headers=LIST_JOBS_HEADERS, tablefmt="grid"))
    return 0


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the quantum volume benchmark.

    Returns:
        Parsed arguments as an argparse.Namespace object.
    """
    parser = argparse.ArgumentParser(description="Metriq-Gym benchmarking CLI")
    subparsers = parser.add_subparsers(dest="action", required=True, help="Action to perform")

    # Subparser for dispatch.
    dispatch_parser = subparsers.add_parser("dispatch", help="Dispatch jobs")
    dispatch_parser.add_argument(
        "input_file",
        type=str,
        help="Path to the file containing the benchmark parameters",
    )
    dispatch_parser.add_argument(
        "-n", "--num_qubits", type=int, default=8, help="Number of qubits (default is 8)"
    )
    dispatch_parser.add_argument(
        "-s", "--shots", type=int, default=8, help="Number of shots per trial (default is 8)"
    )
    dispatch_parser.add_argument(
        "-t", "--trials", type=int, default=8, help="Number of trials (default is 8)"
    )
    dispatch_parser.add_argument(
        "-p",
        "--provider",
        type=str,
        choices=ProviderType.value_list(),
        default="ibmq",
        help="String identifier for backend provider service",
    )
    dispatch_parser.add_argument(
        "-d",
        "--device",
        type=str,
        default="qasm_simulator",
        help='Backend to use (default is "qasm_simulator")',
    )

    # Subparser for poll.
    poll_parser = subparsers.add_parser("poll", help="Poll jobs")
    poll_parser.add_argument("--job_id", type=str, required=True, help="Job ID to poll")

    # Subparser for list-jobs.
    subparsers.add_parser("list-jobs", help="List dispatched jobs")

    return parser.parse_args()
