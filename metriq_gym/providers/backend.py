from typing import Any
from qiskit import QuantumCircuit


class ProviderJob:
    def status(self) -> str:
        raise NotImplementedError

    def result(self) -> Any:
        raise NotImplementedError

    def job_id(self) -> str:
        raise NotImplementedError

    def in_final_state(self) -> bool:
        raise NotImplementedError


class Backend:
    def __init__(self, backend_name: str):
        self.backend_name = backend_name

    def run(self, circuits: list[QuantumCircuit], shots: int) -> ProviderJob:
        raise NotImplementedError

    def transpile_circuit(self, circuit: QuantumCircuit) -> QuantumCircuit:
        raise NotImplementedError

    def get_job(self, provider_job_id: str) -> ProviderJob:
        raise NotImplementedError
