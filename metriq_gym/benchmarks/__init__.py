from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkData
from metriq_gym.benchmarks.qml_kernel import QMLKernel, QMLKernelData
from metriq_gym.benchmarks.quantum_volume import QuantumVolume, QuantumVolumeData
from metriq_gym.benchmarks.bseq import BSEQ, BSEQData
from metriq_gym.job_type import JobType

BENCHMARK_HANDLERS: dict[JobType, type[Benchmark]] = {
    JobType.QUANTUM_VOLUME: QuantumVolume,
    JobType.BSEQ: BSEQ,
    JobType.QML_KERNEL: QMLKernel,
}

BENCHMARK_DATA_CLASSES: dict[JobType, type[BenchmarkData]] = {
    JobType.QUANTUM_VOLUME: QuantumVolumeData,
    JobType.BSEQ: BSEQData,
    JobType.QML_KERNEL: QMLKernelData,
}

SCHEMA_MAPPING = {
    JobType.QUANTUM_VOLUME: "quantum_volume.schema.json",
    JobType.BSEQ: "bseq.schema.json",
    JobType.QML_KERNEL: "qml_kernel.schema.json",
}
