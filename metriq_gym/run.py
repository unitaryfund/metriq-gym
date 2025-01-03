import argparse
import sys
import logging
from tabulate import tabulate
from dotenv import load_dotenv

from metriq_gym.benchmarks.handlers import HANDLERS
from metriq_gym.job_manager import JobManager
from metriq_gym.cli import parse_arguments
from metriq_gym.job_type import JobType
from metriq_gym.schema_validator import load_and_validate

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main() -> int:
    """Main entry point for the CLI."""
    load_dotenv()
    args = parse_arguments()
    job_manager = JobManager()

    if args.action == "dispatch":
        params = load_and_validate(args.input_file)

        handler = HANDLERS[JobType(params["benchmark_name"])](args, params, job_manager)
        handler.dispatch_handler()

    elif args.action == "poll":
        job_id = args.job_id
        job = job_manager.get_job(job_id)
        job_type = job["job_type"]

        handler = HANDLERS[JobType(job_type)](args, None, job_manager)
        handler.poll_handler()

    elif args.action == "list-jobs":
        list_jobs(args, job_manager)

    else:
        logging.error("Invalid action specified. Run with --help for usage information.")
        return 1

    return 0


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
    headers = ["ID", "Backend", "Type", "Provider", "Misc"]
    table = [
        [
            job.get("id", ""),
            job.get("backend", ""),
            job.get("job_type", ""),
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


if __name__ == "__main__":
    sys.exit(main())
