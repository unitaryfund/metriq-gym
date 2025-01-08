import argparse
from typing import Any

from metriq_gym.providers.backend import Backend
from metriq_gym.providers.provider import Provider


class Benchmark:
    def __init__(
        self,
        args: argparse.Namespace,
        params: dict[str, Any],
    ):
        self.args = args
        self.params = params

    def dispatch_handler(self, provider: Provider, backend: Backend) -> dict[str, Any]:
        raise NotImplementedError

    def poll_handler(self, provider: Provider, backend: Backend, job: dict[str, Any]) -> None:
        raise NotImplementedError
