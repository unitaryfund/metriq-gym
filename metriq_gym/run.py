import argparse
from dataclasses import asdict
from datetime import datetime
import sys
import logging
import uuid

from dotenv import load_dotenv
from qbraid import JobStatus, ResultData
from qbraid.runtime import QuantumDevice, QuantumProvider, load_job

from metriq_gym.benchmarks import BENCHMARK_DATA_CLASSES, BENCHMARK_HANDLERS
from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkData
from metriq_gym.cli import list_jobs, parse_arguments
from metriq_gym.job_manager import JobManager, MetriqGymJob
from metriq_gym.provider import QBRAID_PROVIDERS, ProviderType
from metriq_gym.schema_validator import load_and_validate
from metriq_gym.job_type import JobType

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def setup_device(provider_name: str, backend_name: str) -> QuantumDevice:
    provider: QuantumProvider = QBRAID_PROVIDERS[ProviderType(provider_name)]
    return provider().get_device(backend_name)


def setup_benchmark(args, params, job_type: JobType) -> Benchmark:
    return BENCHMARK_HANDLERS[job_type](args, params)


def setup_job_data_class(job_type: JobType) -> type[BenchmarkData]:
    return BENCHMARK_DATA_CLASSES[job_type]


def dispatch_job(args: argparse.Namespace, job_manager: JobManager) -> None:
    logger.info("Dispatching job...")
    provider_name = args.provider
    device_name = args.device
    device = setup_device(provider_name, device_name)
    params = load_and_validate(args.input_file)
    job_type = JobType(params.benchmark_name)
    handler: Benchmark = setup_benchmark(args, params, job_type)
    job_data: BenchmarkData = handler.dispatch_handler(device)
    job_id = job_manager.add_job(
        MetriqGymJob(
            id=str(uuid.uuid4()),
            job_type=job_type,
            params=params.model_dump(),
            data=asdict(job_data),
            provider_name=provider_name,
            device_name=device_name,
            dispatch_time=datetime.now(),
        )
    )
    logger.info(f"Job dispatched with ID: {job_id}")


def poll_job(args: argparse.Namespace, job_manager: JobManager) -> None:
    if not args.job_id:
        jobs = job_manager.get_jobs()
        if not jobs:
            print("No jobs available for polling.")
            return
        print("Available jobs:")
        list_jobs(jobs, show_index=True)
        while True:
            try:
                selected_index = int(input("Select a job index: "))
                if 0 <= selected_index < len(jobs):
                    break
                else:
                    print(f"Invalid index. Please enter a number between 0 and {len(jobs) - 1}")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        args.job_id = jobs[selected_index].id

    logger.info("Polling job...")
    metriq_job: MetriqGymJob = job_manager.get_job(args.job_id)
    job_type: JobType = JobType(metriq_job.job_type)
    job_data: BenchmarkData = setup_job_data_class(job_type)(**metriq_job.data)
    handler = setup_benchmark(args, None, job_type)
    quantum_job = [
        load_job(job_id, provider=metriq_job.provider_name, **asdict(job_data))
        for job_id in job_data.provider_job_ids
    ]
    if all(task.status() == JobStatus.COMPLETED for task in quantum_job):
        result_data: list[ResultData] = [task.result().data for task in quantum_job]
        handler.poll_handler(job_data, result_data)
    else:
        logger.info("Job is not yet completed. Please try again later.")


def main() -> int:
    """Main entry point for the CLI."""
    load_dotenv()
    args = parse_arguments()
    job_manager = JobManager()

    if args.action == "dispatch":
        dispatch_job(args, job_manager)
    elif args.action == "poll":
        poll_job(args, job_manager)
    elif args.action == "list-jobs":
        jobs: list[MetriqGymJob] = job_manager.get_jobs()
        list_jobs(jobs)

    else:
        logging.error("Invalid action specified. Run with --help for usage information.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
