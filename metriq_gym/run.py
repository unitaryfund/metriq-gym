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
    params = load_and_validate(args.input_file)
    job_manager = JobManager(args.jobs_file)

    handler = HANDLERS[JobType(params["benchmark_name"])](args, params, job_manager)

    if args.action == "dispatch":
        handler.dispatch_handler()
    elif args.action == "poll":
        handler.poll_handler()
    else:
        logging.error("Invalid action specified. Use 'dispatch' or 'poll'.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
