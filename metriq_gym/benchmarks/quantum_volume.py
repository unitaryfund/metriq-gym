import logging

from metriq_gym.bench import dispatch_bench_job
from metriq_gym.stats import calc_stats

from metriq_gym.benchmarks.benchmark import Benchmark
from metriq_gym.process import poll_job_results


class QuantumVolume(Benchmark):
    def dispatch_handler(self) -> None:
        result = dispatch_bench_job(
            self.params["num_qubits"],
            self.args.backend,
            self.params["shots"],
            self.params["trials"],
            self.args.provider,
        )

        if len(result.counts) > 0:
            stats = calc_stats([result])
            logging.info(f"Simulator-only job completed: {stats[0]}.")
            print(stats[0])
            return

        logging.info(f"Dispatched {self.params["trials"]} trials in 1 job.")

        self.job_manager.add_job(result.to_serializable())

        logging.info(f"Done writing job IDs to file {self.args.jobs_file}.")

    def poll_handler(self) -> None:
        logging.info("Polling for job results.")
        results = poll_job_results(self.args.jobs_file, self.args.job_id)
        result_count = len(results)
        logging.info(f"Found {result_count} completed jobs.")
        if result_count == 0:
            logging.info("No new results: done.")

        stats = calc_stats(results)
        logging.info(f"Processed {len(stats)} new results.")

        for s in stats:
            logging.info(f"Aggregated results over {s['trials']} trials: {s}")
