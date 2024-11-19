"""Poll IBM-Q cloud services for job results"""

import os
import logging
import sys

from qiskit_ibm_runtime import QiskitRuntimeService
from dotenv import load_dotenv

from metriq_gym.process import poll_job_results, calc_stats
from metriq_gym.parse import parse_arguments
from metriq_gym.bench import BenchJobType


load_dotenv()
logging.basicConfig(level=logging.INFO)


def main():
    args = parse_arguments()

    QiskitRuntimeService.save_account(
        channel="ibm_quantum",
        token=os.environ.get("IBM_QISKIT_API_KEY"),
        set_as_default=True,
        overwrite=True,
    )

    logging.info("Polling for job results.")
    results = poll_job_results(args.jobs_file, BenchJobType.QV)
    result_count = len(results)
    logging.info(f"Found {result_count} completed jobs.")
    if result_count == 0:
        logging.info("No new results: done.")
        return 0

    stats = calc_stats(results, args.confidence_level)
    logging.info(f"Processed {len(stats)} new results.")

    for s in stats:
        logging.info(f"Aggregated results over {s['trials']} trials: {s}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
