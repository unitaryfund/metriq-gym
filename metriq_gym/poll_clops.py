"""Poll cloud services for CLOPS job results."""

import os
import logging
import sys

from qiskit_ibm_runtime import QiskitRuntimeService
from dotenv import load_dotenv

from metriq_gym.cli import parse_arguments
from metriq_gym.process import poll_job_results
from metriq_gym.bench import BenchJobType
from qiskit_device_benchmarking.clops.clops_benchmark import clops_benchmark


load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    args = parse_arguments()

    if args.token and args.instance:
        QiskitRuntimeService.save_account(
            channel="ibm_quantum",
            token=os.environ.get("IBM_QISKIT_API_KEY"),
            instance=args.instance,
            set_as_default=True,
            overwrite=True,
        )

    logging.info("Polling for CLOPS job results.")
    results = poll_job_results(args.jobs_file, BenchJobType.CLOPS)
    result_count = len(results)
    logging.info(f"Found {result_count} completed jobs.")
    if result_count == 0:
        logging.info("No new results: done.")
        return 0

    for result in results:
        clops = clops_benchmark(
            service=QiskitRuntimeService(),
            backend_name=result.backend,
            width=result.qubits,
            layers=result.qubits,
            shots=result.shots,
            num_circuits=result.trials,
            job=result.job,
        )

        result_str = f"Measured clops of {clops.job_attributes['backend_name']} is {clops.clops()}"
        logging.info(result_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
