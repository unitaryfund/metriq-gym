"""Command-line parsing for running metriq benchmarks."""

import argparse

from tabulate import tabulate

from metriq_gym.job_manager import JobManager, MetriqGymJob
from metriq_gym.provider import ProviderType

LIST_JOBS_HEADERS = ["ID", "Provider", "Device", "Type", "Dispatch time (UTC)"]


def list_jobs(job_manager: JobManager) -> None:
    """List jobs recorded in the job manager.

    Args:
        job_manager: Job manager instance.
    """
    # Retrieve all jobs from JobManager.
    jobs: list[MetriqGymJob] = job_manager.get_jobs()

    # Display jobs in a tabular format.
    if not jobs:
        print("No jobs found.")
        return

    print(
        tabulate([job.to_table_row() for job in jobs], headers=LIST_JOBS_HEADERS, tablefmt="grid")
    )


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
