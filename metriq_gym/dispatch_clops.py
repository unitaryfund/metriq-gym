"""Dispatch a CLOPS job with CLI parameters to Qiskit and wait for result."""

import json
import logging
import os
import sys
from dotenv import load_dotenv


from qiskit_ibm_runtime import QiskitRuntimeService

from metriq_gym.parse import parse_arguments
from metriq_gym.bench import BenchJobResult, BenchJobType, BenchProvider
from metriq_gym.hardware.clops_benchmark import clops_benchmark


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

    logging.info(
        f"Dispatching CLOPS job with n={args.num_qubits}, shots={args.shots}, backend={args.backend}, trials={args.trials}, jobs_file={args.jobs_file}"
    )

    clops = clops_benchmark(
        service=QiskitRuntimeService(),
        backend_name=args.backend,
        width=args.num_qubits,
        layers=args.num_qubits,
        num_circuits=args.trials,
        shots=args.shots,
    )

    partial_result = BenchJobResult(
        provider_job_id=clops.job.job_id(),
        backend=args.backend,
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

    # Convert dataclass to string (JSON)
    result_json = json.dumps(partial_result.to_serializable())

    with open(args.jobs_file, "a") as file:
        file.write(str(result_json) + os.linesep)

    logging.info(str(result_json))

    return 0


if __name__ == "__main__":
    sys.exit(main())
