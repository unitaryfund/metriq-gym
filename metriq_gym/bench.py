"""Benchmarking utilities."""

from typing import Any
import os
import random
import time
import qiskit
from dataclasses import dataclass
from enum import IntEnum
from dotenv import load_dotenv

from pyqrack import QrackSimulator
from qiskit_aer import Aer
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit import QuantumCircuit
from qiskit.providers import Job

from qiskit_ionq import IonQProvider

from pytket.extensions.quantinuum.backends.api_wrappers import QuantinuumAPI
from pytket.extensions.quantinuum.backends.credential_storage import (
    QuantinuumConfigCredentialStorage,
)

from pytket.extensions.quantinuum import QuantinuumBackend
from pytket.extensions.qiskit import qiskit_to_tk

from metriq_gym.gates import rand_u3, coupler


load_dotenv()


class BenchProvider(IntEnum):
    IBMQ = 0
    QUANTINUUM = 1
    IONQ = 2


class BenchJobType(IntEnum):
    QV = 0
    CLOPS = 1


@dataclass
class BenchJobResult:
    """Data structure to hold results from the dispatch_bench_job function."""

    provider_job_id: str
    provider: BenchProvider
    backend: str
    job_type: BenchJobType
    qubits: int
    shots: int
    depth: int
    ideal_probs: list[dict[int, float]]
    counts: list[dict[str, int]]
    interval: float
    sim_interval: float
    trials: int
    job: Job | None = None

    def to_serializable(self) -> dict[str, Any]:
        """Return a dictionary excluding non-serializable fields (like 'job')."""
        return {
            "provider_job_id": self.provider_job_id,
            "provider": self.provider.name,
            "backend": self.backend,
            "job_type": self.job_type.name,
            "qubits": self.qubits,
            "shots": self.shots,
            "depth": self.depth,
            "ideal_probs": self.ideal_probs,
            "counts": self.counts,
            "interval": self.interval,
            "sim_interval": self.sim_interval,
            "trials": self.trials,
        }


def get_backend(provider: str, backend_name: str):
    match provider.lower():
        case "ibmq":
            return (
                Aer.get_backend(backend_name)
                if Aer.backends(backend_name)
                else QiskitRuntimeService().backend(backend_name)
            )
        case "quantinuum":
            return QuantinuumBackend(
                device_name=backend_name,
                api_handler=QuantinuumAPI(token_store=QuantinuumConfigCredentialStorage()),
                attempt_batching=True,
            )
        case "ionq":
            provider = IonQProvider(os.getenv("IONQ_API_KEY"))
            return provider.get_backend(str(backend_name), gateset="native")
        case _:
            raise ValueError(
                f"Unable to retrieve backend. Hardware provider '{provider}' is not supported."
            )


def random_circuit_sampling(n: int) -> QuantumCircuit:
    circ = QuantumCircuit(n)
    for _ in range(n):
        for i in range(n):
            rand_u3(circ, i)

        unused_bits = list(range(n))
        random.shuffle(unused_bits)
        while len(unused_bits) > 1:
            c = unused_bits.pop()
            t = unused_bits.pop()
            coupler(circ, c, t)
    return circ


def transpile_circuit(circ: QuantumCircuit, provider: str, backend_name: str) -> QuantumCircuit:
    backend = get_backend(provider, backend_name)
    match provider:
        case "ibmq":
            circ = qiskit.compiler.transpile(circ, backend)
        case "quantinuum":
            circ = backend.get_compiled_circuit(qiskit_to_tk(circ))
        case "ionq":
            circ = qiskit.compiler.transpile(circ, backend)
        case _:
            raise ValueError(f"Unable to transpile circuit. Provider {provider} is not supported.")
    return circ


def prepare_circuits(
    n: int, trials: int, provider: str, backend_name: str
) -> tuple[list[QuantumCircuit], list[float], float]:
    circs = []
    ideal_probs = []
    sim_interval = 0

    for _ in range(trials):
        circ = random_circuit_sampling(n)
        sim_circ = circ.copy()
        circ.measure_all()

        transpiled_circ = transpile_circuit(circ, provider, backend_name)
        circs.append(transpiled_circ)

        start = time.perf_counter()
        sim = QrackSimulator(n)
        sim.run_qiskit_circuit(sim_circ, shots=0)
        ideal_probs.append(sim.out_probs())
        del sim
        sim_interval += time.perf_counter() - start

    return circs, ideal_probs, sim_interval


def dispatch_bench_job(
    n: int, backend: str, shots: int, trials: int, provider="ibmq"
) -> BenchJobResult:
    """Run quantum volume benchmark using QrackSimulator and return structured results.

    Args:
        n: Number of qubits in the quantum circuit.
        backend: Backend name to use for the execution (e.g., 'qasm_simulator').
        shots: Number of measurement shots to perform on the quantum circuit.
        trials: Number of circuits to run.

    Returns:
        A BenchJobResult instance containing:
        - id : Job ID string.
        - backend: Back end ID string.
        - job_type: Type of benchmark.
        - provider: Provider ID enum.
        - ideal_probs: A dictionary mapping bitstrings to probabilities.
        - counts: A dictionary mapping bitstrings to the counts measured from the backend.
        - interval: The time taken for the backend execution (in seconds).
        - sim_interval: The time taken for the simulation using Qrack (in seconds).
        - trials: Number of circuits run.
    """
    provider = provider.lower()
    device = get_backend(provider, backend)
    circs, ideal_probs, sim_interval = prepare_circuits(n, trials, provider, backend)

    match provider:
        case "ibmq":
            job = device.run(circs, shots=shots)
            job_id = job.job_id()
            provider = BenchProvider.IBMQ
        case "quantinuum":
            job = device.process_circuits(circs, n_shots=shots)
            job_id = job
            provider = BenchProvider.QUANTINUUM
        case "ionq":
            job = device.run(circs, shots=shots)
            job_id = job._job_id
            provider = BenchProvider.IONQ
        case _:
            raise ValueError(f"Unable to launch job. Provider {provider} unsupported.")

    partial_result = BenchJobResult(
        provider_job_id=job_id,
        provider=provider,
        backend=backend,
        job_type=BenchJobType.QV,
        qubits=n,
        shots=shots,
        depth=n,
        ideal_probs=ideal_probs,
        sim_interval=sim_interval,
        counts=[],
        interval=0,
        trials=trials,
        job=job,
    )

    if provider == "ibmq" and backend == "qasm_simulator":
        result = job.result()
        partial_result.counts = result.get_counts()
        partial_result.interval = result.time_taken

    return partial_result
