"""Dispatch job with CLI parameters to Qiskit."""
import json
import logging
import os
import sys

from dataclasses import asdict

from qiskit_ibm_runtime import QiskitRuntimeService

from metriq_gym.bench import dispatch_bench_job
from metriq_gym.parse import parse_arguments
from metriq_gym.process import calc_stats


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    args = parse_arguments()

    if args.token:
        QiskitRuntimeService.save_account(channel="ibm_quantum", token=args.token, set_as_default=True, overwrite=True)

    logging.info(f"Dispatching Quantum Volume job with n={args.n}, shots={args.shots}, trials={args.trials}, backend={args.backend}, confidence_level={args.confidence_level}, jobs_file={args.jobs_file}")

    result = dispatch_bench_job(args.n, args.backend, args.shots, args.trials)

    if len(result.counts) > 0:
        stats = calc_stats([result], args.confidence_level)
        logging.info(f"Simulator-only job completed: {stats[0]}.")
        print(stats[0])

        return 0

    logging.info(f"Dispatched {args.trials} trials in 1 job.")

    # Convert dataclass to string (JSON)
    result_json = json.dumps(asdict(result))

    with open(args.jobs_file, "a") as file:
        file.write(str(result_json) + os.linesep)

    logging.info(f"Done writing job IDs to file {args.jobs_file}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
