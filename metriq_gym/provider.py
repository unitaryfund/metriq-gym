from typing import Callable
from qbraid import (
    QbraidJob,
    QbraidDevice,
    QbraidProvider,
    QuantumDevice,
    QuantumJob,
    QuantumProvider,
)
from qbraid.runtime import (
    QiskitRuntimeProvider,
    QiskitBackend,
    IonQDevice,
    IonQProvider,
    BraketProvider,
    BraketDevice,
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


def create_braket_job(job_id, device: BraketDevice = None):
    return BraketQuantumTask(job_id)


def create_qiskit_job(job_id, device: QiskitBackend = None):
    return QiskitJob(job_id)


def create_ionq_job(job_id, device: IonQDevice):
    return IonQJob(job_id, session=device.session)


def create_qbraid_job(job_id, device: QbraidDevice):
    return QbraidJob(job_id, device=device)


QBRAID_PROVIDERS: dict[
    ProviderType, tuple[QuantumProvider, Callable[[str, QuantumDevice], QuantumJob]]
] = {
    ProviderType.AWS: (BraketProvider, create_braket_job),
    ProviderType.IBMQ: (QiskitRuntimeProvider, create_qiskit_job),
    ProviderType.IONQ: (IonQProvider, create_ionq_job),
    ProviderType.QBRAID: (QbraidProvider, create_qbraid_job),
}
