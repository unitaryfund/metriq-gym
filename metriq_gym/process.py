"""Benchmark processing and calculation utilities."""
import json
import math
import statistics

from scipy.stats import binom

from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.providers import Job, JobStatus

from metriq_gym.bench import BenchJobResult, BenchJobType, BenchProvider

def get_job(result: BenchJobResult) -> Job:
    if result.provider == BenchProvider.IBMQ:
        return QiskitRuntimeService().job(result.id)

    raise ValueError(f"Cannot find provider {result.provider}.")


def get_job_result(job: Job, partial_result: BenchJobResult):
    result = job.result()
    partial_result.counts = result.get_counts()
    partial_result.interval = result.time_taken

    return partial_result


def poll_job_results(jobs_file: str, job_type: BenchJobType) -> list[BenchJobResult]:
    """Run quantum volume benchmark using QrackSimulator and return structured results."""
    
    results = []    
    lines_out = []
    
    with open(jobs_file, 'r') as file:
        lines = file.readlines()
        for line in lines:
            result_data = json.loads(line)
            # Recreate BenchJobResult without the job field
            result = BenchJobResult(
                id=result_data['id'],
                provider=BenchProvider[result_data['provider']],
                backend=result_data['backend'],
                job_type=BenchJobType[result_data['job_type']],
                qubits=result_data['qubits'],
                shots=result_data['shots'],
                depth=result_data['depth'],
                ideal_probs=result_data['ideal_probs'],
                counts=result_data['counts'],
                interval=result_data['interval'],
                sim_interval=result_data['sim_interval'],
            )
            
            job = get_job(result)
            status = job.status()
            
            if (status == JobStatus.RUNNING) or (result.job_type != job_type):
                # Still running
                lines_out.append(line)
            elif status == JobStatus.DONE:
                # Success
                result.job = job
                if job_type == BenchJobType.QV:
                    result = get_job_result(job, result)
                results.append(result)
            else:
                # Failure
                print(f"Job ID {job.job_id()} failed with status: {status}.")
    
    # Write back the jobs still running to the file
    with open(jobs_file, "w") as file:
        file.writelines(lines_out)
    
    return results


def calc_trial_stats(ideal_probs: dict[int, float], counts: dict[str, int], interval: float, 
               sim_interval: float, shots: int, confidence_level: float) -> dict[str, float]:
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
    numer = 0
    denom = 0
    sum_hog_counts = 0
    for i in range(n_pow):
        b = (bin(i)[2:]).zfill(n)

        count = counts[b] if b in counts else 0
        ideal = ideal_probs[i]

        # XEB / EPLG
        denom = denom + (ideal - u_u) ** 2
        numer = numer + (ideal - u_u) * ((count / shots) - u_u)

        # QV / HOG
        if ideal > threshold:
            sum_hog_counts += count

    hog_prob = sum_hog_counts / shots
    xeb = numer / denom
    p_val = (1 - binom.cdf(sum_hog_counts - 1, shots, 1 / 2).item()) if sum_hog_counts > 0 else 1

    return {
        "qubits": n,
        "shots": shots,
        "seconds": interval,
        "xeb": xeb,
        "sim_seconds": sim_interval,
        "hog_prob": hog_prob,
        "pass": hog_prob >= 2 / 3,
        "p-value": p_val,
        "confidence_level": confidence_level,
        "confidence_pass": p_val < confidence_level,
        "clops": (n * shots) / interval,
        "sim_clops": (n * shots) / sim_interval,
        "eplg": (1 - (xeb ** (1 / n))) if xeb < 1 else 0
    }

def calc_stats(results: list[BenchJobResult], confidence_level: float) -> dict:
    to_ret = []
    for result in results:
        stats = calc_trial_stats(result.ideal_probs[0], result.counts[0], result.interval, result.sim_interval, result.shots, confidence_level)
        stats["trials"] = len(result.counts)

        if stats["trials"] == 1:
            to_ret.append(stats)
            
            continue

        stats["trial_p-values"] = []
        for trial in range(1, stats["trials"]):
            s = calc_trial_stats(result.ideal_probs[trial], result.counts[trial], result.interval, result.sim_interval, result.shots, confidence_level)
            stats["hog_prob"] += + s["hog_prob"]
            stats["p-value"] *= s["p-value"]
            stats["trial_p-values"].append(s["p-value"])
            stats["pass"] &= s["pass"]
            stats["confidence_pass"] &= s["confidence_pass"]

        stats["hog_prob"] /= stats["trials"]
        stats["p-value"] = stats["p-value"] ** (1 / stats["trials"])
        stats["clops"] = (result.depth * result.shots * stats["trials"]) / stats["seconds"]
        stats["sim_clops"] = (result.depth * result.shots * stats["trials"]) / stats["sim_seconds"]
        
        to_ret.append(stats)
    
    return to_ret
