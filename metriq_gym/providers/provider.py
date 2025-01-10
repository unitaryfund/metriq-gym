from enum import StrEnum
from typing import Any


class ProviderType(StrEnum):
    IBMQ = "ibmq"
    IONQ = "ionq"

    @classmethod
    def list(cls):
        return [provider.value for provider in cls]


class Provider:
    def get_backend(backend_name: str) -> Any:
        raise NotImplementedError
