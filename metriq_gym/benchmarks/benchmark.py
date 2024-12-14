import argparse
from typing import Any

from metriq_gym.job_manager import JobManager


class Benchmark:
    def __init__(self, args: argparse.Namespace, params: dict[str, Any], job_manager: JobManager):
        self.args = args
        self.params = params
        self.job_manager = job_manager

    def dispatch_handler(self) -> None:
        raise NotImplementedError

    def poll_handler(self) -> None:
        raise NotImplementedError
