import argparse
from dataclasses import dataclass

from pydantic import BaseModel
from qbraid import QuantumDevice, ResultData


@dataclass
class BenchmarkData:
    provider_job_id: str


class Benchmark:
    def __init__(
        self,
        args: argparse.Namespace,
        params: BaseModel,
    ):
        self.args = args
        self.params: BaseModel = params

    def dispatch_handler(self, device: QuantumDevice) -> BenchmarkData:
        raise NotImplementedError

    def poll_handler(
        self,
        job_data: BenchmarkData,
        result_data: ResultData,
    ) -> None:
        raise NotImplementedError
