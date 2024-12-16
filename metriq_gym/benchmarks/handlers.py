from metriq_gym.benchmarks.benchmark import Benchmark
from metriq_gym.benchmarks.clops import CLOPS
from metriq_gym.benchmarks.quantum_volume import QuantumVolume
from metriq_gym.job_type import JobType

HANDLERS: dict[JobType, type[Benchmark]] = {
    JobType.QUANTUM_VOLUME: QuantumVolume,
    JobType.CLOPS: CLOPS,
}
