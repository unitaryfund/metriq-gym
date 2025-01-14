import argparse
from dataclasses import asdict
import sys
import logging

from dotenv import load_dotenv
from qbraid import QuantumJob, ResultData
from qbraid.runtime import QuantumDevice, QuantumProvider

from metriq_gym.benchmarks import BENCHMARK_DATA_CLASSES, BENCHMARK_HANDLERS
from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkData
from metriq_gym.cli import list_jobs, parse_arguments
from metriq_gym.job_manager import JobManager
from metriq_gym.provider import QBRAID_PROVIDERS, ProviderType
from metriq_gym.schema_validator import load_and_validate
from metriq_gym.job_type import JobType


def setup_device(provider_name: str, backend_name: str) -> tuple:
    provider: QuantumProvider = QBRAID_PROVIDERS[ProviderType(provider_name)]["provider"]
    device: QuantumDevice = provider().get_device(backend_name)
    return device


def setup_handler(args, params, job_type) -> type[Benchmark]:
    return BENCHMARK_HANDLERS[job_type](args, params)


def setup_job_class(provider_name: str) -> type[QuantumJob]:
    return QBRAID_PROVIDERS[ProviderType(provider_name)]["job_class"]


def create_job_data(job_type: JobType, job_data: dict) -> BenchmarkData:
    job_data_class = BENCHMARK_DATA_CLASSES[job_type]
    return job_data_class(**job_data)


def dispatch_job(args: argparse.Namespace, job_manager: JobManager) -> None:
    provider_name, backend_name = args.provider, args.backend
    device = setup_device(provider_name, backend_name)
    params = load_and_validate(args.input_file)
    job_type = JobType(params.benchmark_name)
    handler: Benchmark = setup_handler(args, params, job_type)
    job_data: BenchmarkData = handler.dispatch_handler(device)
    job_manager.add_job(
        {
            "provider": provider_name,
            "device": backend_name,
            **params.model_dump(),
            "data": asdict(job_data),
        }
    )


def poll_job(args: argparse.Namespace, job_manager: JobManager) -> None:
    metriq_job = job_manager.get_job(args.job_id)
    job_type: JobType = JobType(metriq_job["benchmark_name"])
    job_data: BenchmarkData = create_job_data(job_type, metriq_job["data"])
    job_class = setup_job_class(metriq_job["provider"])
    device = setup_device(metriq_job["provider"], metriq_job["device"])
    handler = setup_handler(args, None, job_type)
    result_data: ResultData = (
        job_class(job_id=job_data.provider_job_id, device=device).result().data
    )
    handler.poll_handler(job_data, result_data)


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
        list_jobs(args, job_manager)

    else:
        logging.error("Invalid action specified. Run with --help for usage information.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
