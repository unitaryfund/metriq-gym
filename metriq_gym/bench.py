import time
import random

from pyqrack import QrackSimulator
from qiskit_aer import Aer
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit import QuantumCircuit
from qiskit.compiler import transpile

from metriq_gym.gates import rand_u3, coupler


def bench_qrack(n: int, backend: str, shots: int) -> tuple[dict[int, float], dict[str, int], float, float]:
    """Run quantum volume benchmark using QrackSimulator and return the results.

    Args:
        n: Number of qubits in the quantum circuit.
        backend: Backend name to use for the execution (e.g., 'qasm_simulator').
        shots: Number of measurement shots to perform on the quantum circuit.

    Returns:
        A tuple containing:
        - A dictionary mapping bitstrings to probabilities (ideal probabilities).
        - A dictionary mapping bitstrings to the counts measured from the backend.
        - The time taken for the backend execution (in seconds).
        - The time taken for the simulation using Qrack (in seconds).
    """
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

    start = time.perf_counter()
    sim = QrackSimulator(n)
    sim.run_qiskit_circuit(circ, shots=0)
    ideal_probs = sim.out_probs()
    del sim
    sim_interval = time.perf_counter() - start

    circ.measure_all()

    device = Aer.get_backend(backend) if len(Aer.backends(backend)) > 0 else QiskitRuntimeService().backend(backend)
    circ = transpile(circ, device, layout_method="noise_adaptive")

    result = device.run(circ, shots=shots).result()
    counts = result.get_counts(circ)
    interval = result.time_taken

    return ideal_probs, counts, interval, sim_interval
