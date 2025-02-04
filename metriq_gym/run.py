from typing import Any
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
    """Initialize and return a QuantumDevice using the specified provider and backend.

    Args:
        provider_name: The name of the quantum provider.
        backend_name: The name of the quantum backend device.

    Returns:
        An instance of the quantum device initialized with the specified provider and backend.
    """
    provider: QuantumProvider = QBRAID_PROVIDERS[ProviderType(provider_name)]
    return provider().get_device(backend_name)


def setup_benchmark(
    args: argparse.Namespace, params: dict[str, Any] | None, job_type: JobType
) -> Benchmark:
    """Set up and return a benchmark handler based on the provided arguments, parameters, and job type.

    Args:
        args: Command-line arguments.
        params: Parameters loaded from the input file, validated against the expected schema.
        job_type: The type of job or benchmark to run.

    Returns:
        An instance of the benchmark handler for the specified job type.
    """
    return BENCHMARK_HANDLERS[job_type](args, params)


def setup_job_data_class(job_type: JobType) -> type[BenchmarkData]:
    """Retrieve and return the data class associated with the specified job type.

    Args:
        job_type: The job type for which the corresponding data class is needed.

    Returns:
        The data class corresponding to the given job type.
    """
    return BENCHMARK_DATA_CLASSES[job_type]


def dispatch_job(args: argparse.Namespace, job_manager: JobManager) -> None:
    """Dispatch a quantum job using the provided arguments and record it in the job manager.

    This function performs the following steps:
      1. Initializes the quantum device based on provider and device names.
      2. Loads and validates benchmark parameters from the input file.
      3. Sets up the benchmark handler.
      4. Dispatches the job to the quantum device.
      5. Records the dispatched job in the job manager with a unique job ID.

    Args:
        args: Command-line arguments containing job configuration.
        job_manager: The job manager used to store and track dispatched jobs.
    """
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
    """Poll the status of a previously dispatched quantum job and process the results if completed.

    This function performs the following:
      1. Retrieves the job information from the job manager.
      2. Reconstructs the job data class instance from stored job data.
      3. Loads the quantum job(s) corresponding to the provider job IDs.
      4. Checks if all quantum tasks are completed.
      5. If completed, retrieves result data and invokes the benchmark's poll handler.
      6. Logs a message if the job is not yet completed.

    Args:
        args: Command-line arguments containing the job ID to poll.
        job_manager: The job manager used to retrieve job information.
    """
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
    """Main entry point for the command-line interface (CLI).

    This function performs the following steps:
      1. Loads environment variables.
      2. Parses command-line arguments.
      3. Initializes the job manager.
      4. Dispatches, polls, or lists jobs based on the specified action.

    Returns:
        Exit code for the CLI application (0 for success, 1 for error).
    """
    load_dotenv()
    args = parse_arguments()
    job_manager = JobManager()

    if args.action == "dispatch":
        dispatch_job(args, job_manager)
    elif args.action == "poll":
        poll_job(args, job_manager)
    elif args.action == "list-jobs":
        list_jobs(job_manager)

    else:
        logging.error("Invalid action specified. Run with --help for usage information.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
