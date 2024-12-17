import sys
import logging
from dotenv import load_dotenv

from metriq_gym.benchmarks.handlers import HANDLERS
from metriq_gym.job_manager import JobManager
from metriq_gym.cli import parse_arguments
from metriq_gym.job_type import JobType
from metriq_gym.schema_validator import load_and_validate

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
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

        handler = HANDLERS[job_type](args, None, job_manager)
        handler.poll_handler()
    else:
        logging.error("Invalid action specified. Use 'dispatch' or 'poll'.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
