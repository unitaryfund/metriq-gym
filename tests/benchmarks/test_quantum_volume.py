from metriq_gym.benchmarks.quantum_volume import calc_stats, QuantumVolumeData


def test_calc_stats():
    job_data = QuantumVolumeData(
        provider_job_id="test_job_id",
        qubits=2,
        shots=100,
        depth=2,
        confidence_level=0.7,
        ideal_probs=[
            {0: 0.8, 1: 0.2},
            {0: 0.6, 1: 0.4},
        ],
        trials=2,
    )
    counts = [
        {"0": 80, "1": 20},
        {"0": 60, "1": 40},
    ]
    stats = calc_stats(job_data, counts)
    assert stats.confidence_pass is True  # All trials pass confidence level

    job_data.confidence_level = 0.9
    stats = calc_stats(job_data, counts)
    assert stats.confidence_pass is False  # Not all trials pass confidence level
