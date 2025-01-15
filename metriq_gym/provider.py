from qbraid import QbraidJob, QbraidProvider
from qbraid.runtime import (
    QiskitRuntimeProvider,
    IonQProvider,
    BraketProvider,
    QiskitJob,
    IonQJob,
    BraketQuantumTask,
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


QBRAID_PROVIDERS = {
    ProviderType.AWS: {
        "provider": BraketProvider,
        "job_class": BraketQuantumTask,
    },
    ProviderType.IBMQ: {
        "provider": QiskitRuntimeProvider,
        "job_class": QiskitJob,
    },
    ProviderType.IONQ: {
        "provider": IonQProvider,
        "job_class": IonQJob,
    },
    ProviderType.QBRAID: {
        "provider": QbraidProvider,
        "job_class": QbraidJob,
    },
}
