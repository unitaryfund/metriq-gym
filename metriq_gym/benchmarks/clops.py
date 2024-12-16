import logging
from qiskit_ibm_runtime import QiskitRuntimeService

from metriq_gym.bench import BenchJobResult, BenchJobType, BenchProvider
from metriq_gym.process import poll_job_results

from qiskit_device_benchmarking.clops.clops_benchmark import clops_benchmark
from metriq_gym.benchmarks.benchmark import Benchmark


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
            backend=self.args.backend,
            provider=BenchProvider.IBMQ,
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
        results = poll_job_results(self.args.jobs_file, BenchJobType.CLOPS)
        result_count = len(results)
        logging.info(f"Found {result_count} completed jobs.")
        if result_count == 0:
            logging.info("No new results: done.")

        for result in results:
            clops = clops_benchmark(
                service=QiskitRuntimeService(),
                backend_name=result.backend,
                width=result.qubits,
                layers=result.qubits,
                shots=result.shots,
                num_circuits=result.trials,
            )

            result_str = (
                f"Measured clops of {clops.job_attributes['backend_name']} is {clops.clops()}"
            )
            logging.info(result_str)
