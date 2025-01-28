from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
from typing import Any
from metriq_gym.job_type import JobType


@dataclass
class MetriqGymJob:
    id: str
    job_type: JobType
    params: dict[str, Any]
    data: dict[str, Any]
    provider_name: str
    device_name: str
    dispatch_time: datetime

    def to_table_row(self) -> list[str]:
        return [
            self.id,
            self.provider_name,
            self.device_name,
            self.job_type,
            self.dispatch_time.isoformat(),
        ]

    def serialize(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, default=str)

    @staticmethod
    def deserialize(data: str) -> "MetriqGymJob":
        job_dict = json.loads(data)
        job = MetriqGymJob(**job_dict)
        job.job_type = JobType(job_dict["job_type"])
        job.dispatch_time = datetime.fromisoformat(job_dict["dispatch_time"])
        return job


# TODO: https://github.com/unitaryfund/metriq-gym/issues/51
class JobManager:
    jobs: list[MetriqGymJob]
    jobs_file = ".metriq_gym_jobs.jsonl"

    def __init__(self):
        self._load_jobs()

    def _load_jobs(self):
        self.jobs = []
        if os.path.exists(self.jobs_file):
            with open(self.jobs_file) as file:
                for line in file:
                    try:
                        job = MetriqGymJob.deserialize(line.strip())
                        self.jobs.append(job)
                    except json.JSONDecodeError:
                        continue

    def add_job(self, job: MetriqGymJob) -> str:
        self.jobs.append(job)
        with open(self.jobs_file, "a") as file:
            file.write(job.serialize() + "\n")
        return job.id

    def get_jobs(self) -> list[MetriqGymJob]:
        return self.jobs

    def get_job(self, job_id: str) -> MetriqGymJob:
        for job in self.jobs:
            if job.id == job_id:
                return job
        raise ValueError(f"Job with id {job_id} not found")
