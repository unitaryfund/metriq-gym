import json
import os
import uuid
from typing import Any

# TODO: https://github.com/unitaryfund/metriq-gym/issues/51


class JobManager:
    def __init__(self):
        self.jobs_file = ".metriq_gym_jobs.jsonl"
        self._load_jobs()

    def _load_jobs(self):
        self.jobs = []
        if os.path.exists(self.jobs_file):
            with open(self.jobs_file) as file:
                for line in file:
                    try:
                        job = json.loads(line.strip())
                        self.jobs.append(job)
                    except json.JSONDecodeError:
                        continue

    def _save_jobs(self):
        with open(self.jobs_file, "w") as file:
            for job in self.jobs:
                file.write(json.dumps(job, sort_keys=True) + "\n")

    def add_job(self, job: dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job["id"] = job_id
        self.jobs.append(job)
        with open(self.jobs_file, "a") as file:
            file.write(json.dumps(job, sort_keys=True) + "\n")
        return job_id

    def remove_job(self, job_id: str):
        self.jobs = [job for job in self.jobs if job["id"] != job_id]
        self._save_jobs()

    def update_job(self, job_id: str, updates: dict[str, Any]):
        for job in self.jobs:
            if job["id"] == job_id:
                job.update(updates)
                break
        self._save_jobs()

    def get_jobs(self) -> list[dict[str, Any]]:
        return self.jobs

    def get_job(self, job_id: str) -> dict[str, Any]:
        for job in self.jobs:
            if job["id"] == job_id:
                return job
        raise ValueError(f"Job with id {job_id} not found")
