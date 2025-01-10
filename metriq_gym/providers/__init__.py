from qbraid.runtime import QiskitRuntimeProvider
from qbraid.runtime import IonQProvider
from metriq_gym.providers.provider import ProviderType

PROVIDERS = {
    ProviderType.IBMQ: QiskitRuntimeProvider,
    ProviderType.IONQ: IonQProvider,
}
