"""Quantum volume + CLOPS in Qiskit."""
import math
import statistics
import logging
from scipy.stats import binom

from qiskit_ibm_runtime import QiskitRuntimeService

from metriq_gym.bench import bench_qrack
from metriq_gym.parse import parse_arguments


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def calc_stats(ideal_probs: dict[int, float], counts: dict[str, int], interval: float, 
               sim_interval: float, shots: int, confidence_level: float) -> dict[str, float]:
    """
    Calculate statistics for quantum volume benchmarking.

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
        - sim_seconds: Time taken for simulation using Qrack.
        - hog_prob: Probability of measuring heavy outputs.
        - pass: Boolean indicating whether the heavy output probability exceeds 2/3.
        - p-value: p-value for the heavy output count.
        - clops: Classical logical operations per second.
        - sim_clops: Simulation classical logical operations per second.
    """
    n_pow = len(ideal_probs)
    n = int(round(math.log2(n_pow)))
    threshold = statistics.median(ideal_probs)
    sum_hog_counts = 0
    for i in range(n_pow):
        b = (bin(i)[2:]).zfill(n)

        if b not in counts:
            continue

        if ideal_probs[i] > threshold:
            sum_hog_counts += counts[b]

    hog_prob = sum_hog_counts / shots
    p_val = (1 - binom.cdf(sum_hog_counts - 1, shots, 1 / 2).item()) if sum_hog_counts > 0 else 1

    return {
        "qubits": n,
        "seconds": interval,
        "sim_seconds": sim_interval,
        "hog_prob": hog_prob,
        "pass": hog_prob >= 2 / 3,
        "p-value": p_val,
        "confidence_level": confidence_level,
        "confidence_pass": p_val < confidence_level,
        "clops": (n * shots) / interval,
        "sim_clops": (n * shots) / sim_interval
    }


def main():
    args = parse_arguments()

    if args.token:
        QiskitRuntimeService.save_account(channel="ibm_quantum", token=args.token, set_as_default=True, overwrite=True)

    logging.info(f"Running quantum volume benchmark with n={args.n}, shots={args.shots}, backend={args.backend}, confidence_level={args.confidence_level}")
    result = bench_qrack(args.n, args.backend, args.shots)
    stats = calc_stats(result.ideal_probs, result.counts, result.interval, result.sim_interval, args.shots, args.confidence_level)
    stats["trials"] = args.trials

    if args.trials == 1:
        logging.info(f"Single trial results: {stats}")
        print(stats)

        return 0

    stats["trial_p-values"] = []
    for trial in range(1, args.trials):
        r = bench_qrack(args.n, args.backend, args.shots)
        s = calc_stats(r.ideal_probs, r.counts, r.interval, r.sim_interval, args.shots, args.confidence_level)
        stats["seconds"] += s["seconds"]
        stats["sim_seconds"] += + s["sim_seconds"]
        stats["hog_prob"] += + s["hog_prob"]
        stats["p-value"] *= s["p-value"]
        stats["trial_p-values"].append(s["p-value"])
        stats["pass"] &= s["pass"]
        stats["confidence_pass"] &= s["confidence_pass"]

    stats["hog_prob"] /= args.trials
    stats["p-value"] = stats["p-value"] ** (1 / args.trials)
    stats["clops"] = (args.n * args.shots * args.trials) / stats["seconds"]
    stats["sim_clops"] = (args.n * args.shots * args.trials) / stats["sim_seconds"]

    logging.info(f"Aggregated results over {args.trials} trials: {stats}")
    print(stats)


if __name__ == "__main__":
    main()
