import argparse
import logging
from typing import Any

from metriq_gym.job_manager import JobManager
from metriq_gym.process import poll_job_results


class Benchmark:
    def __init__(self, args: argparse.Namespace, params: dict[str, Any], job_manager: JobManager):
        self.args = args
        self.params = params
        self.job_manager = job_manager

    def dispatch_handler(self) -> None:
        raise NotImplementedError

    def poll_handler(self) -> None:
        logging.info("Polling for job results.")
        results = poll_job_results(self.args.jobs_file, self.args.job_id)
        result_count = len(results)
        logging.info(f"Found {result_count} completed jobs.")

        if result_count == 0:
            logging.info("No new results: done.")

        print(results)
        return results
