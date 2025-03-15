import argparse
from typing import Generic, TypeVar

from pydantic import BaseModel
from dataclasses import dataclass

from qbraid import GateModelResultData, QuantumDevice, QuantumJob


@dataclass
class BenchmarkData:
    """Stores intermediate data from pre-processing and dispatching"""

    provider_job_ids: list[str]


@dataclass
class BenchmarkResult:
    """Stores the final results of the benchmark"""

    pass


BD = TypeVar("BD", bound=BenchmarkData)
BR = TypeVar("BR", bound=BenchmarkResult)


class Benchmark(Generic[BD, BR]):
    def __init__(
        self,
        args: argparse.Namespace,
        params: BaseModel,
    ):
        self.args = args
        self.params: BaseModel = params

    def dispatch_handler(self, device: QuantumDevice) -> BD:
        raise NotImplementedError

    def poll_handler(
        self,
        job_data: BD,
        result_data: list[GateModelResultData],
        quantum_jobs: list[QuantumJob],
    ) -> BR:
        raise NotImplementedError
