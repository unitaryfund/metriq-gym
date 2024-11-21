import json
import uuid
from typing import List, Dict, Any

DEFAULT_FILE_PATH = ".metric_gym_jobs.jsonl"

# TODO: JobManager is not thread-safe at the moment


class JobManager:
    def __init__(self, file_path: str = DEFAULT_FILE_PATH):
        self.file_path = file_path
        self._load_jobs()

    def _load_jobs(self):
        self.jobs = []
        try:
            with open(self.file_path, "r") as file:
                for line in file:
                    try:
                        job = json.loads(line.strip())
                        self.jobs.append(job)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            self.jobs = []

    def _save_jobs(self):
        with open(self.file_path, "w") as file:
            for job in self.jobs:
                file.write(json.dumps(job, sort_keys=True) + "\n")

    def add_job(self, job: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job["id"] = job_id
        self.jobs.append(job)
        with open(self.file_path, "a") as file:
            file.write(json.dumps(job, sort_keys=True) + "\n")
        return job_id

    def remove_job(self, job_id: str):
        self.jobs = [job for job in self.jobs if job["id"] != job_id]
        self._save_jobs()

    def update_job(self, job_id: str, updates: Dict[str, Any]):
        for job in self.jobs:
            if job["id"] == job_id:
                job.update(updates)
                break
        self._save_jobs()

    def get_jobs(self) -> List[Dict[str, Any]]:
        return self.jobs

    def get_job(self, job_id: str) -> Dict[str, Any]:
        for job in self.jobs:
            if job["id"] == job_id:
                return job
        raise ValueError(f"Job with id {job_id} not found")
