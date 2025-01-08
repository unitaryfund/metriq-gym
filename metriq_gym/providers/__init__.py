from metriq_gym.providers.ibmq import IBMQProvider
from metriq_gym.providers.ionq import IonQProvider
from metriq_gym.providers.provider import ProviderType
from metriq_gym.providers.quantinuum import QuantinuumProvider

PROVIDERS = {
    ProviderType.IBMQ: IBMQProvider,
    ProviderType.IONQ: IonQProvider,
    ProviderType.QUANTINUUM: QuantinuumProvider,
    # ProviderType.AWS: AWSProvider,
}
