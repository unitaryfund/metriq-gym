"""Quantum volume + CLOPS + EPLG in Qiskit."""
import math
import statistics
import logging

from scipy.stats import binom

from qiskit_ibm_runtime import QiskitRuntimeService

from metriq_gym.bench import bench_qrack
from metriq_gym.parse import parse_arguments


logging.basicConfig(level=logging.INFO)


def calc_stats(ideal_probs: dict[int, float], counts: dict[str, int], interval: float, 
               sim_interval: float, shots: int) -> dict[str, float]:
    """Calculate various statistics for quantum volume benchmarking.

    Args:
        ideal_probs: A dictionary of bitstrings to ideal probabilities.
        counts: A dictionary of bitstrings to counts measured from the backend.
        interval: Time taken by the backend for execution (in seconds).
        sim_interval: Time taken for Qrack simulation (in seconds).
        shots: Number of measurement shots performed on the quantum circuit.

    Returns:
        A dictionary of statistics, including:
        - qubits: Number of qubits used in the circuit.
        - seconds: Time taken for backend execution.
        - xeb: Cross Entropy Benchmarking score.
        - hog_prob: Probability of measuring heavy outputs.
        - pass: Boolean indicating whether the heavy output probability exceeds 2/3.
        - p-value: p-value for the heavy output count.
        - clops: Classical logical operations per second.
        - sim_clops: Simulation classical logical operations per second.
        - eplg: Estimated Pauli Layer Gate (EPLG) fidelity.
    """
    n_pow = len(ideal_probs)
    n = int(round(math.log2(n_pow)))
    threshold = statistics.median(ideal_probs)
    u_u = statistics.mean(ideal_probs)
    e_u = 0
    m_u = 0
    sum_hog_counts = 0
    for i in range(n_pow):
        b = (bin(i)[2:]).zfill(n)

        if b not in counts:
            continue

        count = counts[b]
        ideal = ideal_probs[i]
        e_u += ideal ** 2
        m_u += ideal * (count / shots)

        if ideal > threshold:
            sum_hog_counts += count

    hog_prob = sum_hog_counts / shots
    xeb = (m_u - u_u) * (e_u - u_u) / ((e_u - u_u) ** 2)
    p_val = (1 - binom.cdf(sum_hog_counts - 1, shots, 1 / 2)) if sum_hog_counts > 0 else 1

    return {
        "qubits": n,
        "seconds": interval,
        "xeb": xeb,
        "hog_prob": hog_prob,
        "pass": hog_prob >= 2 / 3,
        "p-value": p_val,
        "clops": (n * shots) / interval,
        "sim_clops": (n * shots) / sim_interval,
        "eplg": (1 - xeb) ** (1 / n) if xeb < 1 else 0
    }


def main() -> None:
    """Main function to execute the quantum volume benchmark."""
    args = parse_arguments()

    if args.token:
        QiskitRuntimeService.save_account(channel="ibm_quantum", token=args.token, set_as_default=True)

    logging.info(f"Running with n={args.n}, shots={args.shots}, backend={args.backend}")

    results = bench_qrack(args.n, args.backend, args.shots)
    ideal_probs, counts, interval, sim_interval = results
    stats = calc_stats(ideal_probs, counts, interval, sim_interval, args.shots)

    logging.info(stats)


if __name__ == "__main__":
    main()
