import os
from typing import Any
from metriq_gym.providers.provider import Provider
from metriq_gym.providers.backend import Backend


class IonQackend(Backend):
    def __init__(self, backend_name: Any):
        super.__init__(backend_name)
        self.backend = IonQProvider(os.getenv("IONQ_API_KEY")).get_backend(
            str(backend_name), gateset="native"
        )


class IonQProvider(Provider):
    def get_backend(self, backend_name: str) -> IonQackend:
        return IonQackend(backend=backend_name)
