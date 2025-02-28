from enum import StrEnum


class ProviderType(StrEnum):
    # Values of the enum need to be consistent with qBraid's entry-points
    # https://github.com/qBraid/qBraid/blob/c6ec0a6fb48d4132c97d48845b6a630800578b78/pyproject.toml#L79-L85
    # TODO: Consider moving this to a shared location
    AWS = "aws"  # supports IQM, QuEra, Rigetti devices
    AZURE = "azure"  # supports Rigetti, Quantinuum, IonQ devices
    IBMQ = "ibm"
    IONQ = "ionq"
    QBRAID = "qbraid"

    @classmethod
    def value_list(cls):
        return [provider.value for provider in cls]
