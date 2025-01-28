from qbraid import (
    QbraidProvider,
    QuantumProvider,
)
from qbraid.runtime import (
    QiskitRuntimeProvider,
    IonQProvider,
    BraketProvider,
)
from enum import StrEnum


class ProviderType(StrEnum):
    AWS = "aws"
    IBMQ = "ibmq"
    IONQ = "ionq"
    QBRAID = "qbraid"

    @classmethod
    def value_list(cls):
        return [provider.value for provider in cls]


QBRAID_PROVIDERS: dict[ProviderType, QuantumProvider] = {
    ProviderType.AWS: BraketProvider,
    ProviderType.IBMQ: QiskitRuntimeProvider,
    ProviderType.IONQ: IonQProvider,
    ProviderType.QBRAID: QbraidProvider,
}
