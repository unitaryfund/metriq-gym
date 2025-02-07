from unittest.mock import patch
import pytest
from datetime import datetime
from metriq_gym.job_manager import JobManager, MetriqGymJob
from tests.test_schema_validator import TEST_BENCHMARK_NAME, TestJobType


@pytest.fixture(autouse=True)
def patch_job_type_enum():
    with patch("metriq_gym.job_manager.JobType", TestJobType):
        yield


@pytest.fixture
def job_manager(tmpdir):
    jobs_file = tmpdir.join("test_jobs.jsonl")
    JobManager.jobs_file = str(jobs_file)
    return JobManager()


@pytest.fixture
def sample_job():
    return MetriqGymJob(
        id="test_job_id",
        provider_name="test_provider",
        device_name="test_device",
        job_type=TestJobType(TEST_BENCHMARK_NAME),
        params={},
        data={},
        dispatch_time=datetime.now(),
    )


def test_load_jobs_empty_file(job_manager):
    assert job_manager.get_jobs() == []


def test_add_job(job_manager, sample_job):
    job_manager.add_job(sample_job)
    jobs = job_manager.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == sample_job.id


def test_load_jobs_with_existing_data(job_manager, sample_job):
    job_manager.add_job(sample_job)
    new_job_manager = JobManager()
    jobs = new_job_manager.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == sample_job.id
