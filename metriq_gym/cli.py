"""Command-line parsing for running metriq benchmarks."""

import argparse

from tabulate import tabulate

from metriq_gym.job_manager import JobManager
from metriq_gym.providers.provider import ProviderType


def list_jobs(args: argparse.Namespace, job_manager: JobManager) -> int:
    """List jobs recorded in the job manager.

    Args:
        args: Parsed arguments.
        job_manager: Job manager instance.
    Returns:
        Return code.
    """
    # Retrieve all jobs from JobManager.
    jobs = job_manager.get_jobs()

    # Apply filters if specified.
    if args.filter and args.value:
        jobs = [job for job in jobs if str(job.get(args.filter, "")).lower() == args.value.lower()]

    # Display jobs in a tabular format.
    if not jobs:
        print("No jobs found.")
        return 0

    # Prepare data for tabulation.
    headers = ["ID", "Device", "Type", "Provider", "Misc"]
    table = [
        [
            job.get("id", ""),
            job.get("device", ""),
            job.get("benchmark_name", ""),
            job.get("provider", ""),
            ", ".join(
                f"{key}: {job[key]}"
                for key in ["qubits", "shots"]
                if key in job and job[key] is not None
            ),
        ]
        for job in jobs
    ]

    # Print the table.
    print(tabulate(table, headers=headers, tablefmt="grid"))
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
        choices=ProviderType.list(),
        default="ibmq",
        help="String identifier for backend provider service",
    )
    dispatch_parser.add_argument(
        "-b",
        "--backend",
        type=str,
        default="qasm_simulator",
        help='Backend to use (default is "qasm_simulator")',
    )
    dispatch_parser.add_argument(
        "-c",
        "--confidence_level",
        type=float,
        default=0.025,
        help="p-value confidence level to use (default is 0.025)",
    )
    dispatch_parser.add_argument(
        "--token", type=str, help="IBM Quantum API token (must be supplied to run on real hardware)"
    )
    dispatch_parser.add_argument(
        "--instance",
        type=str,
        help="Name of the IBM Quantum plan instance (e.g. 'ibm-q/open/main')",
    )

    # Subparser for poll.
    poll_parser = subparsers.add_parser("poll", help="Poll jobs")
    poll_parser.add_argument("--job_id", type=str, required=True, help="Job ID to poll")

    # Subparser for list-jobs.
    list_jobs_parser = subparsers.add_parser("list-jobs", help="List dispatched jobs")
    list_jobs_parser.add_argument(
        "--filter",
        type=str,
        choices=["backend", "job_type", "provider"],
        help="Filter jobs by a specific field (e.g., backend, job_type, provider)",
    )
    list_jobs_parser.add_argument(
        "--value",
        type=str,
        help="Value to match for the specified filter (used with --filter)",
    )

    return parser.parse_args()
