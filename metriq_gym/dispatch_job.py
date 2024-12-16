import logging
import sys

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

    HANDLERS[JobType(params["benchmark_name"])](args, params, job_manager).dispatch_handler()

    return 0


if __name__ == "__main__":
    sys.exit(main())
