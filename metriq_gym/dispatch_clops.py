"""Dispatch a CLOPS job with CLI parameters to Qiskit and wait for result."""
import json
import logging
import os

from dataclasses import asdict

from qiskit_ibm_runtime import QiskitRuntimeService

from metriq_gym.parse import parse_arguments
from metriq_gym.bench import BenchJobResult, BenchJobType, BenchProvider
from metriq_gym.hardware.clops_benchmark import clops_benchmark


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    args = parse_arguments()

    if not args.token:
        raise ValueError("CLOPS benchmark requires an IBMQ token!")

    QiskitRuntimeService.save_account(channel="ibm_quantum", token=args.token, set_as_default=True, overwrite=True)

    logging.info(f"Dispatching CLOPS job with n={args.n}, shots={args.shots}, trials={args.trials}, backend={args.backend}, confidence_level={args.confidence_level}, jobs_file={args.jobs_file}")

    clops = clops_benchmark(
        QiskitRuntimeService(),
        args.backend,
        width = args.n,
        layers = args.n,
        shots = args.shots
    )
    
    result = BenchJobResult(
        id = clops.job.job_id(),
        provider = BenchProvider.IBMQ,
        job_type = BenchJobType.CLOPS,
        qubits = clops.job_attributes.width,
        shots = clops.job_attributes.shots,
        depth = clops.job_attributes.layers,
        ideal_probs = [],
        counts = [],
        interval = result.time_taken,
        sim_interval = 0
    )
    result = json.dumps(asdict(result))
    with open(args.jobs_file, "a") as file:
        # Out to file
        file.write(str(result_json) + os.linesep)

    logging.info(str(result_dict))
    print(str(result_dict))

    return 0


if __name__ == "__main__":
    main()
