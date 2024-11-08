"""Benchmarking utilities."""
import random
import time
from dataclasses import dataclass
from enum import IntEnum

from pyqrack import QrackSimulator
from qiskit_aer import Aer
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit import QuantumCircuit
from qiskit.compiler import transpile
from qiskit.providers import Job

from pytket.extensions.quantinuum import QuantinuumBackend
from pytket.extensions.qiskit import qiskit_to_tk

from metriq_gym.gates import rand_u3, coupler


class BenchProvider(IntEnum):
    IBMQ = 1
    QUANTINUUM = 2

class BenchJobType(IntEnum):
    QV = 1
    CLOPS = 2

@dataclass
class BenchJobResult:
    """Data structure to hold results from the dispatch_bench_job function."""
    id: str
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
    job: Job | None = None

    def to_serializable(self):
        """Return a dictionary excluding non-serializable fields (like 'job')."""
        return {
            "id": self.id,
            "provider": self.provider.name,
            "backend": self.backend,
            "job_type": self.job_type.name,
            "qubits": self.qubits,
            "shots": self.shots,
            "depth": self.depth,
            "ideal_probs": self.ideal_probs,
            "counts": self.counts,
            "interval": self.interval,
            "sim_interval": self.sim_interval
        }


def random_circuit_sampling(n: int):
    circ = QuantumCircuit(n)

    lcv_range = range(n)
    all_bits = list(lcv_range)

    for _ in range(n):
        # Single-qubit gates
        for i in lcv_range:
            rand_u3(circ, i)

        # 2-qubit couplers
        unused_bits = all_bits.copy()
        random.shuffle(unused_bits)
        while len(unused_bits) > 1:
            c = unused_bits.pop()
            t = unused_bits.pop()
            coupler(circ, c, t)

    return circ


def dispatch_bench_job(n: int, backend: str, shots: int, trials: int, provider="ibmq") -> BenchJobResult:
    """Run quantum volume benchmark using QrackSimulator and return structured results.

    Args:
        n: Number of qubits in the quantum circuit.
        backend: Backend name to use for the execution (e.g., 'qasm_simulator').
        shots: Number of measurement shots to perform on the quantum circuit.

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
    """
    provider = provider.lower()
    device = None
    if provider == "ibmq":
        device = Aer.get_backend(backend) if len(Aer.backends(backend)) > 0 else QiskitRuntimeService().backend(backend)
    else:
        device = QuantinuumBackend(
            device_name=backend,
            api_handler=QuantinuumAPI(token_store=QuantinuumConfigCredentialStorage()),
            attempt_batching=True
        )

    circs = []
    ideal_probs = []
    sim_interval = 0
    for _ in range(trials):
        circ = random_circuit_sampling(n)
        sim_circ = circ.copy()
        circ.measure_all()

        if provider == "ibmq":
            circ = transpile(circ, device)
        else:
            circ = device.get_compiled_circuit(qiskit_to_tk(circ))

        circs.append(circ)

        start = time.perf_counter()
        sim = QrackSimulator(n)
        sim.run_qiskit_circuit(sim_circ, shots=0)
        ideal_probs.append(sim.out_probs())
        del sim
        sim_interval += time.perf_counter() - start

    job = None
    if provider == "ibmq":
        job = device.run(circs, shots=shots)
    else:
        job = device.process_circuit(circs, n_shots=shots)
        # Try the approach below if the above doesn't work:
        # Since attempt_batching=True,
        # tket should batch these requests,
        # so long as they occur quickly and can be batched.
        # job = []
        # for circ in circs:
        #    job.append(device.process_circuit(circ, n_shots=shots))
    
    partial_result = BenchJobResult(
        id = job.job_id() if provider == "ibmq" else job,
        provider = BenchProvider.IBMQ if provider == "ibmq" else BenchProvider.QUANTINUUM,
        backend = backend,
        job_type = BenchJobType.QV,
        qubits = n,
        shots = shots,
        depth = n,
        ideal_probs=ideal_probs,
        sim_interval=sim_interval,
        counts=[],
        interval=0,
        job=job
    )

    if provider == "ibmq" and backend == "qasm_simulator":
        result = job.result()
        partial_result.counts = result.get_counts()
        partial_result.interval = result.time_taken

    return partial_result
