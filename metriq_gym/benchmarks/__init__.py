from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkData

# from metriq_gym.benchmarks.clops import CLOPS
from metriq_gym.benchmarks.quantum_volume import QuantumVolume, QuantumVolumeData
from metriq_gym.job_type import JobType

BENCHMARK_HANDLERS: dict[JobType, type[Benchmark]] = {
    JobType.QUANTUM_VOLUME: QuantumVolume,
    # JobType.CLOPS: CLOPS,
}

BENCHMARK_DATA_CLASSES: dict[JobType, type[BenchmarkData]] = {
    JobType.QUANTUM_VOLUME: QuantumVolumeData,
    # JobType.CLOPS: CLOPSJobData,
}
