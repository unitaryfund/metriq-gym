import argparse
from dataclasses import dataclass
from typing import Any

from qbraid import QuantumDevice, QuantumProvider


@dataclass
class BenchmarkJobData:
    pass


class Benchmark:
    def __init__(
        self,
        args: argparse.Namespace,
        params: dict[str, Any],
    ):
        self.args = args
        self.params = params

    def dispatch_handler(
        self, provider: QuantumProvider, device: QuantumDevice
    ) -> tuple[BenchmarkJobData, str]:
        raise NotImplementedError

    def poll_handler(
        self,
        provider: QuantumProvider,
        device: QuantumDevice,
        job: dict[str, Any],
        provider_job_id: str,
    ) -> None:
        raise NotImplementedError
