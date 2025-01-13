from dataclasses import asdict
import sys
import logging
from dotenv import load_dotenv
from metriq_gym.benchmarks import HANDLERS
from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkJobData
from metriq_gym.cli import list_jobs, parse_arguments
from metriq_gym.job_manager import JobManager
from metriq_gym.provider import PROVIDERS, ProviderType
from metriq_gym.schema_validator import load_and_validate
from metriq_gym.job_type import JobType
from qbraid.runtime import QuantumDevice, QuantumProvider


def setup_provider_and_device(provider_name: str, backend_name: str) -> tuple:
    provider: QuantumProvider = PROVIDERS[ProviderType(provider_name)]
    device: QuantumDevice = provider().get_device(backend_name)
    return provider, device


def setup_handler(args, params, job_type) -> type[Benchmark]:
    return HANDLERS[JobType(job_type)](args, params)


def main() -> int:
    """Main entry point for the CLI."""
    load_dotenv()
    args = parse_arguments()
    job_manager = JobManager()

    if args.action == "dispatch":
        provider_name, backend_name = args.provider, args.backend
        provider, device = setup_provider_and_device(provider_name, backend_name)
        params = load_and_validate(args.input_file)
        handler = setup_handler(args, params, params["benchmark_name"])
        job_data: BenchmarkJobData
        provider_job_id: str
        job_data, provider_job_id = handler.dispatch_handler(provider, device)
        job_manager.add_job(
            {
                "provider": provider_name,
                "device": backend_name,
                **params,
                "data": {asdict(job_data)},
                "provider_job_id": provider_job_id,
            }
        )
    elif args.action == "poll":
        job_id = args.job_id
        job = job_manager.get_job(job_id)
        provider, device = setup_provider_and_device(job["provider"], job["device"])
        handler = setup_handler(args, None, job["benchmark_name"])
        handler.poll_handler(provider, device, job["data"], job["provider_job_id"])

    elif args.action == "list-jobs":
        list_jobs(args, job_manager)

    else:
        logging.error("Invalid action specified. Run with --help for usage information.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
