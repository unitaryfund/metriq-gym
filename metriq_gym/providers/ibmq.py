from typing import Any
from metriq_gym.providers.provider import Provider, ProviderType
from metriq_gym.providers.backend import Backend, ProviderJob
from qiskit import QuantumCircuit
from qiskit.compiler import transpile
from qiskit_aer import Aer
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.providers import Job


class IBMQJob(ProviderJob):
    def __init__(self, job: Job):
        self.job = job

    def job_id(self) -> str:
        return self.job.job_id()

    def status(self) -> str:
        return self.job.status()

    def result(self) -> Any:
        return self.job.result()


class IBMQBackend(Backend):
    def __init__(self, backend_name: str):
        super().__init__(backend_name)
        self.backend = (
            Aer.get_backend(backend_name)
            if Aer.backends(backend_name)
            else QiskitRuntimeService().backend(backend_name)
        )

    def run(self, circuits: list[QuantumCircuit], shots: int) -> IBMQJob:
        return IBMQJob(self.backend.run(circuits, shots=shots))

    def transpile_circuit(self, circuit: QuantumCircuit) -> QuantumCircuit:
        if self.backend_name == "qasm_simulator":
            return circuit
        return transpile(circuit, self.backend_name)

    def get_job(self, provider_job_id: str) -> Any:
        return IBMQJob(QiskitRuntimeService().job(provider_job_id))


class IBMQProvider(Provider):
    _type = ProviderType.IBMQ

    def get_backend(backend_name: str) -> IBMQBackend:
        return IBMQBackend(backend_name)
