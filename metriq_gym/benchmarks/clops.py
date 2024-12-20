import logging
from qiskit_ibm_runtime import QiskitRuntimeService

from metriq_gym.bench import BenchJobResult, BenchJobType
from metriq_gym.process import poll_job_results
from metriq_gym.benchmarks.benchmark import Benchmark
from metriq_gym.stats import calc_stats

from qiskit_device_benchmarking.clops.clops_benchmark import clops_benchmark


class CLOPS(Benchmark):
    def dispatch_handler(self) -> None:
        clops = clops_benchmark(
            service=QiskitRuntimeService(),
            backend_name=self.args.backend,
            width=self.params["num_qubits"],
            layers=self.params["num_qubits"],
            num_circuits=self.params["trials"],
            shots=self.params["shots"],
        )

        partial_result = BenchJobResult(
            provider_job_id=clops.job.job_id(),
            confidence_level=self.params["confidence_level"],
            backend=self.args.backend,
            provider=self.args.provider,
            job_type=BenchJobType.CLOPS,
            qubits=clops.job_attributes["width"],
            shots=clops.job_attributes["shots"],
            depth=clops.job_attributes["layers"],
            ideal_probs=[],
            counts=[],
            interval=0,
            sim_interval=0,
            trials=clops.job_attributes["num_circuits"],
            job=clops.job,
        )

        self.job_manager.add_job(partial_result.to_serializable())

    def poll_handler(self) -> None:
        logging.info("Polling for CLOPS job results.")
        results = poll_job_results(self.args.jobs_file, self.args.job_id)
        result_count = len(results)
        logging.info(f"Found {result_count} completed jobs.")
        if result_count == 0:
            logging.info("No new results: done.")

        stats = calc_stats(results)
        logging.info(f"Processed {len(stats)} new results.")

        for s in stats:
            logging.info(f"Aggregated results over {s['trials']} trials: {s}")
