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

    result = aer_sim.run(circ, shots=(1 << n)).result()
    counts = result.get_counts(circ)
    interval = result.time_taken

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

    # For QV, we compare probabilities of (ideal) "heavy outputs."
    # If the probability is above 2/3, the protocol certifies/passes the qubit width.
    threshold = statistics.median(ideal_probs)
    u_u = statistics.mean(ideal_probs)
    e_u = 0
    m_u = 0
    sum_hog_counts = 0
    for i in range(n_pow):
        b = (bin(i)[2:]).zfill(n)

        # XEB / EPLG
        if b in counts:
            count = counts[b]
            e_u = e_u + ideal_probs[i] ** 2
            m_u = m_u + ideal_probs[i] * (count / n_pow)

            # QV / HOG
            if ideal_probs[i] > threshold:
                sum_hog_counts = sum_hog_counts + count

    hog_prob = sum_hog_counts / n_pow
    xeb = (m_u - u_u) * (e_u - u_u) / ((e_u - u_u) ** 2)
    p_val = (1 - binom.cdf(sum_hog_counts - 1, n_pow, 1 / 2)) if sum_hog_counts > 0 else 1

    print({
        'qubits': n,
        'seconds': interval,
        'hog_prob': hog_prob,
        'pass': (hog_prob >= 2 / 3),
        'p-value': p_val,
        'clops': ((n * n_pow) / interval),
        'xeb': xeb,
        'eplg': (1 - xeb) ** (1 / n)
    })

    return 0


if __name__ == '__main__':
    sys.exit(main())
