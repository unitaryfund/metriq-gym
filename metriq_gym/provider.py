from enum import StrEnum

from qbraid.runtime import QiskitRuntimeProvider
from qbraid.runtime import IonQProvider


class ProviderType(StrEnum):
    IBMQ = "ibmq"
    IONQ = "ionq"

    @classmethod
    def list(cls):
        return [provider.value for provider in cls]


PROVIDERS = {
    ProviderType.IBMQ: QiskitRuntimeProvider,
    ProviderType.IONQ: IonQProvider,
}
