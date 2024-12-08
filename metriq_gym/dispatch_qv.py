"""Dispatch job with CLI parameters to Qiskit."""

import logging
import sys


from metriq_gym.bench import dispatch_bench_job
from metriq_gym.job_manager import JobManager
from metriq_gym.cli import parse_arguments
from metriq_gym.stats import calc_stats


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    args = parse_arguments()

    logging.info(
        f"Dispatching Quantum Volume job with n={args.num_qubits}, shots={args.shots}, trials={args.trials}, backend={args.backend}, confidence_level={args.confidence_level}, jobs_file={args.jobs_file}"
    )

    job_manager = JobManager(args.jobs_file)

    result = dispatch_bench_job(
        args.num_qubits, args.backend, args.shots, args.trials, args.provider
    )

    if len(result.counts) > 0:
        stats = calc_stats([result], args.confidence_level)
        logging.info(f"Simulator-only job completed: {stats[0]}.")
        print(stats[0])

        return 0

    logging.info(f"Dispatched {args.trials} trials in 1 job.")

    job_manager.add_job(result.to_serializable())

    logging.info(f"Done writing job IDs to file {args.jobs_file}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
