from functools import singledispatch

from qbraid import QuantumJob
from qbraid.runtime import QiskitJob, AzureQuantumJob
from qiskit_ibm_runtime.execution_span import ExecutionSpans


@singledispatch
def execution_time(quantum_job: QuantumJob) -> float:
    raise NotImplementedError(f"Execution time not implemented for type {type(quantum_job)}")


@execution_time.register
def _(quantum_job: QiskitJob) -> float:
    execution_spans: ExecutionSpans = (
        quantum_job._job.result().metadata["execution"]["execution_spans"].sort()
    )
    return (execution_spans.stop - execution_spans.start).total_seconds()


@execution_time.register
def _(quantum_job: AzureQuantumJob) -> float:
    return (
        quantum_job._job.details.end_execution_time - quantum_job._job.details.begin_execution_time
    ).total_seconds()
