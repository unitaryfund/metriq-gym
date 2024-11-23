import pytest
from metriq_gym.stats import calc_trial_stats, calc_stats, TrialStats, AggregateStats
from metriq_gym.bench import BenchJobResult, BenchProvider, BenchJobType


def test_calc_trial_stats():
    """Test calc_trial_stats with sample input."""
    ideal_probs = {0: 0.8, 1: 0.2}
    counts = {"0": 80, "1": 20}
    interval = 10.0
    sim_interval = 5.0
    shots = 100
    confidence_level = 0.05

    result = calc_trial_stats(
        ideal_probs=ideal_probs,
        counts=counts,
        interval=interval,
        sim_interval=sim_interval,
        shots=shots,
        confidence_level=confidence_level,
    )

    assert isinstance(result, TrialStats)
    assert result.qubits == 1  # log2(len(ideal_probs))
    assert result.shots == 100
    assert result.seconds == 10.0
    assert result.sim_seconds == 5.0
    assert result.hog_prob == 0.8
    assert result.hog_pass is True
    assert result.p_value < confidence_level
    assert result.confidence_pass is True


def test_calc_stats_single_trial():
    """Test calc_stats for a single trial."""
    result = BenchJobResult(
        provider_job_id="job-1",
        provider=BenchProvider.IBMQ,
        backend="simulator",
        job_type=BenchJobType.QV,
        qubits=1,
        shots=100,
        depth=10,
        ideal_probs=[{0: 0.8, 1: 0.2}],
        counts=[{"0": 80, "1": 20}],
        interval=10.0,
        sim_interval=5.0,
        trials=1,
    )

    stats = calc_stats(results=[result], confidence_level=0.05)

    assert len(stats) == 1
    aggregate = stats[0]
    assert isinstance(aggregate, AggregateStats)
    assert aggregate.provider == BenchProvider.IBMQ
    assert aggregate.trials == 1
    assert aggregate.hog_prob == 0.8
    assert aggregate.hog_pass is True
    assert aggregate.confidence_pass is True


def test_calc_stats_provider_logic():
    """Test calc_stats with mixed provider logic."""
    ibmq_result = BenchJobResult(
        provider_job_id="job-ibmq",
        provider=BenchProvider.IBMQ,
        backend="simulator",
        job_type=BenchJobType.QV,
        qubits=2,
        shots=200,
        depth=15,
        ideal_probs=[{0: 0.7, 1: 0.3}],
        counts=[{"0": 140, "1": 60}],
        interval=20.0,
        sim_interval=10.0,
        trials=1,
    )

    ionq_result = BenchJobResult(
        provider_job_id="job-ionq",
        provider=BenchProvider.IONQ,
        backend="simulator",
        job_type=BenchJobType.QV,
        qubits=2,
        shots=200,
        depth=15,
        ideal_probs=[{0: 0.7, 1: 0.3}],
        counts=[{"0": 140, "1": 60}],
        interval=20.0,
        sim_interval=10.0,
        trials=1,
    )

    stats = calc_stats(results=[ibmq_result, ionq_result], confidence_level=0.05)

    assert len(stats) == 2
    assert stats[0].provider == BenchProvider.IBMQ
    assert stats[1].provider == BenchProvider.IONQ
    assert stats[0].hog_prob == 0.7
    assert stats[1].hog_prob == 0.7
    assert stats[0].hog_pass is True
    assert stats[1].hog_pass is True


def test_calc_stats_multiple_trials():
    """Test calc_stats for multiple trials."""
    result = BenchJobResult(
        provider_job_id="job-2",
        provider=BenchProvider.IONQ,
        backend="simulator",
        job_type=BenchJobType.QV,
        qubits=1,
        shots=100,
        depth=10,
        ideal_probs=[
            {0: 0.8, 1: 0.2},
            {0: 0.6, 1: 0.4},
        ],
        counts=[
            {"0": 80, "1": 20},
            {"0": 60, "1": 40},
        ],
        interval=15.0,
        sim_interval=7.5,
        trials=2,
    )

    stats = calc_stats(results=[result], confidence_level=0.05)

    assert len(stats) == 1
    aggregate = stats[0]
    assert isinstance(aggregate, AggregateStats)
    assert aggregate.provider == BenchProvider.IONQ
    assert aggregate.trials == 2
    assert aggregate.hog_prob == pytest.approx((0.8 + 0.6) / 2)
    assert aggregate.hog_pass is False  # One trial fails hog_pass
    assert aggregate.confidence_pass is True  # All trials pass confidence level
