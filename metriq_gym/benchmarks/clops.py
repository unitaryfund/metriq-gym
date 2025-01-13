import logging
from typing import Any

from metriq_gym.process import poll_job_results
from metriq_gym.benchmarks.benchmark import Benchmark
from metriq_gym.providers.backend import Backend
from metriq_gym.provider import Provider
from metriq_gym.stats import calc_stats


class CLOPS(Benchmark):
    def poll_handler(
        self, provider: Provider, backend: Backend, job: dict[str, Any], provider_job_id: str
    ) -> None:
        logging.info("Polling for CLOPS job results.")
        results = poll_job_results(self.args.job_id)
        result_count = len(results)
        logging.info(f"Found {result_count} completed jobs.")
        if result_count == 0:
            logging.info("No new results: done.")

        stats = calc_stats(results)
        logging.info(f"Processed {len(stats)} new results.")

        for s in stats:
            logging.info(f"Aggregated results over {s['trials']} trials: {s}")
