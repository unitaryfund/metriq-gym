import math
import statistics
from scipy.stats import binom
from dataclasses import dataclass

from qbraid import QuantumDevice, QuantumJob, ResultData
from qbraid.runtime.result_data import MeasCount
from pyqrack import QrackSimulator
from qiskit import QuantumCircuit

from metriq_gym.circuits import qiskit_random_circuit_sampling

from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkData


@dataclass
class QuantumVolumeData(BenchmarkData):
    qubits: int
    shots: int
    depth: int
    confidence_level: float
    ideal_probs: list[list[float]]
    trials: int


def prepare_qv_circuits(n: int, trials: int) -> tuple[list[QuantumCircuit], list[list[float]]]:
    circuits = []
    ideal_probs = []

    sim = QrackSimulator(n)

    for _ in range(trials):
        circuit = qiskit_random_circuit_sampling(n)
        sim_circuit = circuit.copy()
        circuit.measure_all()
        circuits.append(circuit)

        sim.run_qiskit_circuit(sim_circuit, shots=0)
        ideal_probs.append(sim.out_probs())
        sim.reset_all()

    return circuits, ideal_probs


@dataclass
class TrialStats:
    """Data class to store statistics of a single trial.

    Attributes:
        qubits: Number of qubits used in the circuit.
        shots: Number of measurement shots performed on the quantum circuit.
        xeb: Cross Entropy Benchmarking score.
        hog_prob: Probability of measuring heavy outputs.
        hog_pass: Boolean indicating whether the heavy output probability exceeds 2/3.
        p_value: p-value for the heavy output count.
        confidence_level: Confidence level for benchmarking.
        confidence_pass: Boolean indicating if the p-value is below the confidence level.
        eplg: Error Per Layered Gate (EPLG) fidelity.
    """

    qubits: int
    shots: int
    xeb: float
    hog_prob: float
    hog_pass: bool
    p_value: float
    confidence_level: float
    confidence_pass: bool
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
        hog_pass: Boolean indicating whether all trials exceeded the heavy output probability threshold.
        confidence_pass: Boolean indicating if all trials passed the confidence level.
    """

    trials: int
    trial_p_values: list[float]
    hog_prob: float
    p_value: float
    hog_pass: bool
    confidence_pass: bool


def calc_trial_stats(
    ideal_probs: list[float],
    counts: dict[str, int],
    shots: int,
    confidence_level: float,
) -> TrialStats:
    """Calculate various statistics for quantum volume benchmarking.

    Args:
        ideal_probs: A dictionary of bitstrings to ideal probabilities.
        counts: A dictionary of bitstrings to counts measured from the backend.
        shots: Number of measurement shots performed on the quantum circuit.
        confidence_level: Specified confidence level for the benchmarking.

    Returns:
        A `TrialStats` object containing the calculated statistics.
    """
    n_pow = len(ideal_probs)
    n = int(round(math.log2(n_pow)))
    threshold = statistics.median(ideal_probs)
    u_u = statistics.mean(ideal_probs)
    numer: float = 0
    denom: float = 0
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
        xeb=xeb,
        hog_prob=hog_prob,
        hog_pass=hog_prob >= 2 / 3,
        p_value=p_val,
        confidence_level=confidence_level,
        confidence_pass=p_val < confidence_level,
        eplg=(1 - (xeb ** (1 / n))) if xeb < 1 else 0,
    )


def calc_stats(data: QuantumVolumeData, counts: list[MeasCount]) -> AggregateStats:
    """Calculate aggregate statistics over multiple trials.

    Args:
        data: contains dispatch-time data (input data + ideal probability).
        counts: contains results from the quantum device (one MeasCount per trial).
    Returns:
        A list of `AggregateStats` objects, each containing aggregated statistics for a result.
    """
    trial_stats = []

    num_trials = len(counts)
    # Process each trial, handling provider-specific logic.
    for trial in range(num_trials):
        trial_stat = calc_trial_stats(
            ideal_probs=data.ideal_probs[trial],
            counts=counts[trial],
            shots=data.shots,
            confidence_level=data.confidence_level,
        )
        trial_stats.append(trial_stat)

    # Aggregate the trial statistics.
    hog_prob = sum(stat.hog_prob for stat in trial_stats) / num_trials
    p_value = math.prod(stat.p_value for stat in trial_stats) ** (1 / num_trials)

    return AggregateStats(
        trials=num_trials,
        trial_p_values=[stat.p_value for stat in trial_stats],
        hog_prob=hog_prob,
        p_value=p_value,
        hog_pass=all(stat.hog_pass for stat in trial_stats),
        confidence_pass=all(stat.confidence_pass for stat in trial_stats),
    )


class QuantumVolume(Benchmark):
    def dispatch_handler(self, device: QuantumDevice) -> QuantumVolumeData:
        num_qubits = self.params.num_qubits
        shots = self.params.shots
        trials = self.params.trials
        circuits, ideal_probs = prepare_qv_circuits(num_qubits, trials)
        quantum_job: QuantumJob | list[QuantumJob] = device.run(circuits, shots=shots)
        job_data = QuantumVolumeData(
            provider_job_id=[quantum_job.id]
            if isinstance(quantum_job, QuantumJob)
            else [job.id for job in quantum_job],
            qubits=num_qubits,
            shots=shots,
            depth=num_qubits,
            confidence_level=self.params.confidence_level,
            ideal_probs=ideal_probs,
            trials=trials,
        )
        return job_data

    def poll_handler(self, job_data: BenchmarkData, result_data: list[ResultData]) -> None:
        if not isinstance(job_data, QuantumVolumeData):
            raise TypeError("Expected job_data to be of type QuantumVolumeJobData")

        counts: list[MeasCount]  # one MeasCount per trial

        # AWS vs IBM
        if len(result_data) == 1:
            counts = result_data[0].get_counts()
        else:
            counts = [r.get_counts() for r in result_data]

        stats: AggregateStats = calc_stats(job_data, counts)
        if stats.confidence_pass:
            print(f"Quantum Volume benchmark for {job_data.qubits} qubits passed.")
