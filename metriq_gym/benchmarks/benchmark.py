import argparse

from pydantic import BaseModel
from dataclasses import dataclass
from datetime import datetime

from qbraid import GateModelResultData, QuantumDevice, QuantumJob


@dataclass
class BenchmarkData:
    """Stores intermediate data from pre-processing and dispatching"""

    provider_job_ids: list[str]


@dataclass
class BenchmarkResult:
    """Stores the final results of the benchmark"""

    pass


class Benchmark[BD: BenchmarkData, BR: BenchmarkResult]:
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

    def upload_handler(
        self,
        job_data: BenchmarkData,
        result_data: BenchmarkResult,
        dispatch_time: datetime,
        submission_id: int,
        platform_id: int,
    ) -> bool:
        raise NotImplementedError
