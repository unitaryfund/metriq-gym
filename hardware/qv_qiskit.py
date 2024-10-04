# Quantum volume protocol certification

import math
import random
import statistics
import sys
import time

from scipy.stats import binom

from pyqrack import QrackSimulator

from qiskit import QuantumCircuit
from qiskit.compiler import transpile
from qiskit_aer.backends import AerSimulator


def rand_u3(circ, q):
    th = random.uniform(0, 2 * math.pi)
    ph = random.uniform(0, 2 * math.pi)
    lm = random.uniform(0, 2 * math.pi)
    circ.u(th, ph, lm, q)


def coupler(circ, q1, q2):
    circ.cx(q1, q2)


def bench_qrack(n):
    # This is a "quantum volume" (random) circuit.
    circ = QuantumCircuit(n)

    lcv_range = range(n)
    all_bits = list(lcv_range)

    for d in range(n):
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

    sim = QrackSimulator(n)
    sim.run_qiskit_circuit(circ, shots=0)
    ideal_probs = [(x * (x.conjugate())).real for x in sim.out_ket()]
    del sim

    circ.measure_all()

    aer_sim = AerSimulator()
    circ = transpile(circ, aer_sim)

    start = time.perf_counter()

    result = aer_sim.run(circ, shots=(1 << n)).result()
    counts = result.get_counts(circ)

    interval = time.perf_counter() - start

    return (ideal_probs, counts, interval)


def main():
    n = 20
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    n_pow = 1 << n

    results = bench_qrack(n)

    ideal_probs = results[0]
    counts = results[1]
    interval = results[2]

    # We compare probabilities of (ideal) "heavy outputs."
    # If the probability is above 2/3, the protocol certifies/passes the qubit width.
    threshold = statistics.median(ideal_probs)
    sum_prob = 0
    sum_counts = 0
    for i in range(n_pow):
        b = (bin(i)[2:]).zfill(n)
        if (ideal_probs[i] >= threshold) and (b in counts):
            sum_counts = sum_counts + counts[b]
            sum_prob = sum_prob + (counts[b] / n_pow)

    p_val = (1 - binom.cdf(sum_counts - 1, n_pow, 1 / 2)) if sum_counts > 0 else 1

    print({
        'qubits': n,
        'seconds': interval,
        'hog_prob': sum_prob,
        'pass': (sum_prob >= 2 / 3),
        'p-value': p_val
    })

    return 0


if __name__ == '__main__':
    sys.exit(main())
