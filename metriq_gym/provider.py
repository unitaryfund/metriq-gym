from enum import StrEnum

from qbraid import QbraidProvider
from qbraid.runtime import QiskitRuntimeProvider
from qbraid.runtime import IonQProvider


class ProviderType(StrEnum):
    IBMQ = "ibmq"
    IONQ = "ionq"
    QBRAID = "qbraid"

    @classmethod
    def list(cls):
        return [provider.value for provider in cls]


PROVIDERS = {
    ProviderType.IBMQ: QiskitRuntimeProvider,
    ProviderType.IONQ: IonQProvider,
    ProviderType.QBRAID: QbraidProvider,
}
