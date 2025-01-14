from qbraid import QbraidJob, QbraidProvider
from qbraid.runtime import QiskitRuntimeProvider, IonQProvider, QiskitJob, IonQJob
from enum import Enum


class ProviderType(Enum):
    IBMQ = "ibmq"
    IONQ = "ionq"
    QBRAID = "qbraid"

    @classmethod
    def list(cls):
        return [provider.value for provider in cls]


QBRAID_PROVIDERS = {
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
