import numpy as np
from dataclasses import dataclass

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import unitary_overlap

from qbraid import GateModelResultData, QuantumDevice, QuantumJob

from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkData, BenchmarkResult
from metriq_gym.task_helpers import flatten_counts, flatten_job_ids


@dataclass
class QMLKernelData(BenchmarkData):
    num_qubits: int


@dataclass
class QMLKernelResult(BenchmarkResult):
    accuracy_score: float


def ZZfeature_circuit(N: int) -> QuantumCircuit:
    """Create a ZZ feature map in the same flavor as arXiv:2405.09724

    Parameters:
        N (int): Number of qubits

    Returns:
        QuantumCircuit: Desired circuit
    """
    layer1 = [(kk, kk + 1) for kk in range(0, N - 1, 2)]
    layer2 = [(kk, kk + 1) for kk in range(1, N - 1, 2)]

    xvec = ParameterVector("x", N)
    qc = QuantumCircuit(N)

    # Apply Hadamard gates to all qubits
    qc.h(range(N))

    # Apply Rz rotations parameterized by xvec
    for idx, param in enumerate(xvec):
        qc.rz(param, idx)

    # Apply entangling operations for both layers
    for pair in layer1 + layer2:
        var = (np.pi - xvec[pair[0]]) * (np.pi - xvec[pair[1]])
        qc.cx(pair[0], pair[1])
        qc.rz(var, pair[1])
        qc.cx(pair[0], pair[1])

    return qc


def create_inner_product_circuit(N: int, seed: int) -> QuantumCircuit:
    if seed is not None:
        np.random.seed(seed)

    # Create the ZZ feature map circuit and build the inner-product circuit.
    qc_qml = ZZfeature_circuit(N)
    inner_prod = unitary_overlap(qc_qml, qc_qml, insert_barrier=True)
    inner_prod.measure_all()

    # Assign parameters: using the same parameters for both copies gives perfect overlap.
    # Here we tile a random parameter vector for half the total parameters.
    param_vec = np.tile(2 * np.pi * np.random.random(size=inner_prod.num_parameters // 2), 2)
    inner_prod_bound: QuantumCircuit = inner_prod.assign_parameters(param_vec)
    return inner_prod_bound


def calculate_accuracy_score(N: int, count_results) -> float:
    expected_state = "0" * N
    accuracy_score = count_results.get(expected_state, 0) / sum(count_results.values())
    return accuracy_score


class QMLKernel(Benchmark):
    def dispatch_handler(self, device: QuantumDevice) -> QMLKernelData:
        qc = create_inner_product_circuit(self.params.num_qubits, 0)
        quantum_job: QuantumJob | list[QuantumJob] = device.run(qc, shots=self.params.shots)
        provider_job_ids = flatten_job_ids(quantum_job)
        return QMLKernelData(
            num_qubits=self.params.num_qubits,
            provider_job_ids=provider_job_ids,
        )

    def poll_handler(
        self,
        job_data: BenchmarkData,
        result_data: list[GateModelResultData],
    ) -> QMLKernelResult:
        if not isinstance(job_data, QMLKernelData):
            raise TypeError(f"Expected job_data to be of type {type(QMLKernelData)}")

        return QMLKernelResult(
            accuracy_score=calculate_accuracy_score(
                job_data.num_qubits, flatten_counts(result_data)[0]
            )
        )
