"""Calculation utilities for quantum benchmarks."""

from dataclasses import dataclass
from scipy.stats import binom
import math
import statistics
from metriq_gym.bench import BenchJobResult, BenchProvider


@dataclass
class TrialStats:
    """Data class to store statistics of a single trial.

    Attributes:
        qubits: Number of qubits used in the circuit.
        shots: Number of measurement shots performed on the quantum circuit.
        seconds: Time taken by the backend for execution.
        xeb: Cross Entropy Benchmarking score.
        sim_seconds: Time taken for Qrack simulation.
        hog_prob: Probability of measuring heavy outputs.
        hog_pass: Boolean indicating whether the heavy output probability exceeds 2/3.
        p_value: p-value for the heavy output count.
        confidence_level: Confidence level for benchmarking.
        confidence_pass: Boolean indicating if the p-value is below the confidence level.
        clops: Classical logical operations per second.
        sim_clops: Simulation classical logical operations per second.
        eplg: Estimated Pauli Layer Gate (EPLG) fidelity.
    """

    qubits: int
    shots: int
    seconds: float
    xeb: float
    sim_seconds: float
    hog_prob: float
    hog_pass: bool
    p_value: float
    confidence_level: float
    confidence_pass: bool
    clops: float
    sim_clops: float
    eplg: float


@dataclass
class AggregateStats:
    """Data class to store aggregated statistics over multiple trials.

    Attributes:
        provider: The quantum backend provider for the result.
        trials: Number of trials aggregated.
        trial_p_values: List of p-values for each trial.
        hog_prob: Average probability of measuring heavy outputs across trials.
        p_value: Combined p-value for all trials.
        clops: Classical logical operations per second for all trials.
        sim_clops: Simulation classical logical operations per second for all trials.
        hog_pass: Boolean indicating whether all trials exceeded the heavy output probability threshold.
        confidence_pass: Boolean indicating if all trials passed the confidence level.
    """

    provider: BenchProvider
    trials: int
    trial_p_values: list[float]
    hog_prob: float
    p_value: float
    clops: float
    sim_clops: float
    hog_pass: bool
    confidence_pass: bool


def calc_trial_stats(
    ideal_probs: dict[int, float],
    counts: dict[str, int],
    interval: float,
    sim_interval: float,
    shots: int,
    confidence_level: float,
) -> TrialStats:
    """Calculate various statistics for quantum volume benchmarking.

    Args:
        ideal_probs: A dictionary of bitstrings to ideal probabilities.
        counts: A dictionary of bitstrings to counts measured from the backend.
        interval: Time taken by the backend for execution (in seconds).
        sim_interval: Time taken for Qrack simulation (in seconds).
        shots: Number of measurement shots performed on the quantum circuit.
        confidence_level: Specified confidence level for the benchmarking.

    Returns:
        A `TrialStats` object containing the calculated statistics.
    """
    n_pow = len(ideal_probs)
    n = int(round(math.log2(n_pow)))
    threshold = statistics.median(ideal_probs)
    u_u = statistics.mean(ideal_probs)
    numer = 0
    denom = 0
    sum_hog_counts = 0
    for i in range(n_pow):
        b = (bin(i)[2:]).zfill(n)

        count = counts[b] if b in counts else 0
        ideal = ideal_probs[i]

        # XEB / EPLG.
        denom = denom + (ideal - u_u) ** 2
        numer = numer + (ideal - u_u) * ((count / shots) - u_u)

        # QV / HOG.
        if ideal > threshold:
            sum_hog_counts += count

    hog_prob = sum_hog_counts / shots
    xeb = numer / denom if denom > 0 else 0
    p_val = (1 - binom.cdf(sum_hog_counts - 1, shots, 1 / 2).item()) if sum_hog_counts > 0 else 1

    return TrialStats(
        qubits=n,
        shots=shots,
        seconds=interval,
        xeb=xeb,
        sim_seconds=sim_interval,
        hog_prob=hog_prob,
        hog_pass=hog_prob >= 2 / 3,
        p_value=p_val,
        confidence_level=confidence_level,
        confidence_pass=p_val < confidence_level,
        clops=(n * shots) / interval if interval > 0 else 0,
        sim_clops=(n * shots) / sim_interval if sim_interval > 0 else 0,
        eplg=(1 - (xeb ** (1 / n))) if xeb < 1 else 0,
    )


def calc_stats(results: list[BenchJobResult], confidence_level: float) -> list[AggregateStats]:
    """Calculate aggregate statistics over multiple trials.

    Args:
        results: A list of results from benchmarking, where each result contains trial data.
        confidence_level: Specified confidence level for the benchmarking.

    Returns:
        A list of `AggregateStats` objects, each containing aggregated statistics for a result.
    """
    aggregate_stats = []
    print(results)

    for result in results:
        trial_stats = []

        # Process each trial, handling provider-specific logic.
        for trial in range(len(result.counts)):
            if result.provider is BenchProvider.IONQ:
                # IonQ-specific handling: convert counts into integers.
                counts = {k: int(v) for k, v in result.counts[trial].items()}
            else:
                counts = result.counts[trial]

            trial_stat = calc_trial_stats(
                ideal_probs=result.ideal_probs[trial],
                counts=counts,
                interval=result.interval,
                sim_interval=result.sim_interval,
                shots=result.shots,
                confidence_level=confidence_level,
            )
            trial_stats.append(trial_stat)

        # Aggregate the trial statistics.
        hog_prob = sum(stat.hog_prob for stat in trial_stats) / len(trial_stats)
        p_value = math.prod(stat.p_value for stat in trial_stats) ** (1 / len(trial_stats))
        clops = (result.depth * result.shots * len(trial_stats)) / result.interval
        sim_clops = (result.depth * result.shots * len(trial_stats)) / result.sim_interval

        # Construct the AggregateStats object.
        aggregate_stats.append(
            AggregateStats(
                provider=result.provider,
                trials=len(trial_stats),
                trial_p_values=[stat.p_value for stat in trial_stats],
                hog_prob=hog_prob,
                p_value=p_value,
                clops=clops,
                sim_clops=sim_clops,
                hog_pass=all(stat.hog_pass for stat in trial_stats),
                confidence_pass=all(stat.confidence_pass for stat in trial_stats),
            )
        )

    return aggregate_stats
