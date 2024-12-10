"""Dispatch job with CLI parameters to Qiskit."""

import logging
import sys

from metriq_gym.bench import dispatch_bench_job
from metriq_gym.job_manager import JobManager
from metriq_gym.cli import parse_arguments
from metriq_gym.stats import calc_stats
from metriq_gym.schema_validator import load_and_validate


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    args = parse_arguments()
    params = load_and_validate(args.input_file)

    logging.info(
        f"Dispatching {params['benchmark_name']} job with n={params["num_qubits"]}, shots={params["shots"]}, trials={params["trials"]}, backend={args.backend}, confidence_level={params["confidence_level"]}, jobs_file={args.jobs_file}"
    )

    job_manager = JobManager(args.jobs_file)

    result = dispatch_bench_job(
        params["num_qubits"], args.backend, params["shots"], params["trials"], args.provider
    )

    if len(result.counts) > 0:
        stats = calc_stats([result], params["confidence_level"])
        logging.info(f"Simulator-only job completed: {stats[0]}.")
        print(stats[0])

        return 0

    logging.info(f"Dispatched {params["trials"]} trials in 1 job.")

    job_manager.add_job(result.to_serializable())

    logging.info(f"Done writing job IDs to file {args.jobs_file}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
