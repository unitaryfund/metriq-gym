"""Benchmark processing and calculation utilities."""

import json
import logging

from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.providers import Job, JobStatus

from qiskit_ionq import IonQProvider

from pytket.backends.status import StatusEnum
from pytket.extensions.quantinuum.backends.api_wrappers import QuantinuumAPI
from pytket.extensions.quantinuum.backends.credential_storage import (
    QuantinuumConfigCredentialStorage,
)

from pytket.extensions.quantinuum import QuantinuumBackend

from metriq_gym.job_manager import JobManager
from metriq_gym.bench import BenchJobResult, BenchJobType, BenchProvider


def get_job(result: BenchJobResult) -> Job:
    if result.provider == BenchProvider.IBMQ:
        return QiskitRuntimeService().job(result.provider_job_id)
    elif result.provider == BenchProvider.IONQ:
        backend = IonQProvider().get_backend(result.backend)
        return backend.retrieve_job(result.provider_job_id)
    return result.id


def get_job_result_qiskit(job: Job, partial_result: BenchJobResult):
    result = job.result()
    partial_result.counts = result.get_counts()
    partial_result.interval = result.time_taken

    return partial_result


def get_job_result_quantinuum(job, partial_result: BenchJobResult):
    partial_result.counts = job.get_counts()
    partial_result.interval = -9999

    return partial_result


def poll_job_results(job_id: str) -> list[BenchJobResult]:
    """Run quantum volume benchmark using QrackSimulator and return structured results.
    Args:
        job_id: The metriq-gym ID of job.
    Returns:
        An array of newly-completed BenchJobResult instances.
    """
    results = []
    lines_out = []
    job_manager = JobManager()
    jobs_file = job_manager.jobs_file

    with open(jobs_file, "r") as file:
        lines = file.readlines()
        logging.info("%i job(s) dispatched.", len(lines))
        for line in lines:
            result_data = json.loads(line)
            if result_data["id"] == job_id:
                # Recreate BenchJobResult without the job field
                result = BenchJobResult(
                    provider_job_id=result_data["provider_job_id"],
                    provider=BenchProvider[result_data["provider"]],
                    backend=result_data["backend"],
                    job_type=BenchJobType[result_data["job_type"]],
                    confidence_level=result_data["confidence_level"],
                    qubits=result_data["qubits"],
                    shots=result_data["shots"],
                    depth=result_data["depth"],
                    ideal_probs=result_data["ideal_probs"],
                    counts=result_data["counts"],
                    interval=result_data["interval"],
                    sim_interval=result_data["sim_interval"],
                    trials=result_data["trials"],
                )

                job = get_job(result)

                # IBMQ:
                if result.provider is BenchProvider.IBMQ:
                    status = job.status()
                    if not job.in_final_state():
                        lines_out.append(line)
                    elif status in (JobStatus.DONE, "DONE"):
                        result.job = job
                        if result.job_type == BenchJobType.QV:
                            result = get_job_result_qiskit(job, result)
                        results.append(result)
                    else:
                        logging.warning("Job ID %s failed with status: %s", job.job_id(), status)

                # Quantinuum:
                elif result.provider is BenchProvider.QUANTINUUM:
                    device = QuantinuumBackend(
                        device_name=result.backend,
                        api_handler=QuantinuumAPI(token_store=QuantinuumConfigCredentialStorage()),
                        attempt_batching=True,
                    )
                    status = device.circuit_status(job)
                    if status not in [
                        StatusEnum.COMPLETED,
                        StatusEnum.CANCELLING,
                        StatusEnum.CANCELLED,
                        StatusEnum.ERROR,
                    ]:
                        lines_out.append(line)
                    elif status == StatusEnum.COMPLETED:
                        result.job = device.get_result(job)
                        if result.job_type == BenchJobType.QV:
                            result = get_job_result_quantinuum(job, result)
                        results.append(result)
                    else:
                        logging.warning("Job ID %s failed with status: %s", job, status)

                # IonQ:
                elif result.provider is BenchProvider.IONQ:
                    status = job.status()
                    if not job.in_final_state():
                        lines_out.append(line)
                    elif status in (JobStatus.DONE, "DONE"):
                        result.job = job
                        if result.job_type == BenchJobType.QV:
                            result = get_job_result_qiskit(job, result)
                        results.append(result)
                    else:
                        logging.warning("Job ID %s failed with status: %s", job.job_id(), status)

                # Provider not supported.
                else:
                    raise ValueError("Unable to poll results.")

    # Write back the jobs still active to the file.
    with open(jobs_file, "w") as file:
        file.writelines(lines_out)

    return results
