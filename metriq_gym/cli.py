"""Command-line parsing for running metriq benchmarks."""

import argparse

from tabulate import tabulate

from metriq_gym.job_manager import JobManager, MetriqGymJob
from metriq_gym.provider import ProviderType

LIST_JOBS_HEADERS = ["ID", "Provider", "Device", "Type", "Dispatch time (UTC)"]
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def list_jobs(job_manager: JobManager, show_index: bool = False) -> None:
    """List jobs recorded in the job manager.

    Args:
        job_manager: Job manager instance.
        show_index: Whether to show the job index in the output table.
    """
    # Retrieve all jobs from JobManager.
    jobs: list[MetriqGymJob] = job_manager.get_jobs()

    # Display jobs in a tabular format.
    if not jobs:
        print("No jobs found.")
        return
        
    table_headers = LIST_JOBS_HEADERS.copy()
    if show_index:
        table_headers.insert(0, "Index")
    
    table = [
        [
            i,
            job.id,
            job.provider_name,
            job.device_name,
            job.job_type,
            job.dispatch_time.strftime(TIMESTAMP_FORMAT),
        ] if show_index else [
            job.id,
            job.provider_name,
            job.device_name,
            job.job_type,
            job.dispatch_time.strftime(TIMESTAMP_FORMAT),
        ]
        for i, job in enumerate(jobs)
    ]
    print(tabulate(table, headers=table_headers, tablefmt="grid"))

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
    poll_parser.add_argument("--job_id", type=str, required=False, help="Job ID to poll (optional)")

    # Subparser for list-jobs.
    subparsers.add_parser("list-jobs", help="List dispatched jobs")

    return parser.parse_args()
