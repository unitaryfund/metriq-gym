import argparse
import sys
import json
import logging
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
    job_manager = JobManager(args.jobs_file)

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
        list_jobs(args)

    else:
        logging.error("Invalid action specified. Run with --help for usage information.")
        return 1

    return 0


def list_jobs(args: argparse.Namespace) -> int:
    """List jobs recorded in the jobs file.

    Args:
        args: Parsed arguments.
    Returns:
        Return code.
    """
    # Read jobs from the file.
    try:
        with open(args.jobs_file, "r") as f:
            jobs = [json.loads(line) for line in f]
    except FileNotFoundError:
        logging.error(f"Jobs file not found: {args.jobs_file}")
        return 1
    except json.JSONDecodeError:
        logging.error(f"Error reading jobs from file: {args.jobs_file}")
        return 1

    # Apply filters if specified.
    if args.filter and args.value:
        jobs = [job for job in jobs if str(job.get(args.filter, "")).lower() == args.value.lower()]

    # Display jobs in a tabular format.
    if not jobs:
        print("No jobs found.")
        return 0

    print(f"{"ID":<36} {"Backend":<20} {"Type":<10} {"Provider":<10} {"Qubits":<6} {"Shots":<6}")
    print("-" * 90)
    for job in jobs:
        print(
            f"{job.get("id", ""):<36} {job.get("backend", ""):<20} {job.get("job_type", ""):<10} "
            f"{job.get("provider", ""):<10} {job.get("qubits", ""):<6} {job.get("shots", ""):<6}"
        )


if __name__ == "__main__":
    sys.exit(main())
