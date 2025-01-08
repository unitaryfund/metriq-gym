import sys
import logging
from dotenv import load_dotenv
from metriq_gym.benchmarks import HANDLERS
from metriq_gym.benchmarks.benchmark import Benchmark
from metriq_gym.cli import list_jobs, parse_arguments
from metriq_gym.job_manager import JobManager
from metriq_gym.providers import PROVIDERS
from metriq_gym.providers.provider import ProviderType
from metriq_gym.schema_validator import load_and_validate
from metriq_gym.job_type import JobType

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def setup_provider_and_backend(provider_name: str, backend_name: str) -> tuple:
    provider = PROVIDERS[ProviderType(provider_name)]
    backend = provider.get_backend(backend_name)
    return provider, backend


def setup_handler(args, params, job_type) -> type[Benchmark]:
    return HANDLERS[JobType(job_type)](args, params)


def main() -> int:
    """Main entry point for the CLI."""
    load_dotenv()
    args = parse_arguments()
    job_manager = JobManager()

    if args.action == "dispatch":
        provider_name, backend_name = args.provider, args.backend
        provider, backend = setup_provider_and_backend(provider_name, backend_name)
        params = load_and_validate(args.input_file)
        handler = setup_handler(args, params, params["benchmark_name"])
        partial_result = handler.dispatch_handler(provider, backend)
        job_manager.add_job(
            {
                "provider": provider_name,
                "backend": backend_name,
                **params,
                "data": {**partial_result},
            }
        )
    elif args.action == "poll":
        job_id = args.job_id
        job = job_manager.get_job(job_id)
        provider, backend = setup_provider_and_backend(job["provider"], job["backend"])
        handler = setup_handler(args, None, job["benchmark_name"])
        handler.poll_handler(provider, backend, job["data"])

    elif args.action == "list-jobs":
        list_jobs(args, job_manager)

    else:
        logging.error("Invalid action specified. Run with --help for usage information.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
