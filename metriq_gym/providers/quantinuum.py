from typing import Any

from qiskit import QuantumCircuit
from metriq_gym.circuits import qiskit_to_tk
from metriq_gym.providers.provider import Provider
from metriq_gym.providers.backend import Backend
from pytket.extensions.quantinuum.backends.api_wrappers import QuantinuumAPI
from pytket.extensions.quantinuum.backends.credential_storage import (
    QuantinuumConfigCredentialStorage,
)
from pytket.extensions.quantinuum import QuantinuumBackend as PytketQuantinuumBackend


class QuantinuumBackend(Backend):
    def __init__(self, backend_name: Any):
        super.__init__(backend_name)
        self.backend = PytketQuantinuumBackend(
            device_name=backend_name,
            api_handler=QuantinuumAPI(token_store=QuantinuumConfigCredentialStorage()),
            attempt_batching=True,
        )

    def transpile_circuit(self, circuit: QuantumCircuit) -> QuantumCircuit:
        return self.backend.get_compiled_circuit(qiskit_to_tk(circuit))


class QuantinuumProvider(Provider):
    def get_backend(self, backend_name: str) -> QuantinuumBackend:
        return QuantinuumBackend(backend=backend_name)
