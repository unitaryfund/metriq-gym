import copy
from dataclasses import dataclass
from typing import Optional

import rustworkx as rx
import numpy as np
from qbraid import GateModelResultData, QuantumDevice, QuantumJob
from qiskit import QuantumCircuit
from qiskit_device_benchmarking.clops.clops_benchmark import append_1q_layer

from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkData, BenchmarkResult
from metriq_gym.helpers.execution_time import execution_time
from metriq_gym.helpers.task_helpers import flatten_job_ids
from metriq_gym.helpers.topology_helpers import device_topology


@dataclass
class ClopsData(BenchmarkData):
    pass


@dataclass
class ClopsResult(BenchmarkResult):
    clops_score: float


def create_qubit_map(width, topology_graph: rx.PyGraph, faulty_qubits, total_qubits):
    """
    Returns a list of  'width' qubits that are connected based on a coupling map that has
    bad edges already removed and a list of faulty qubits.  If there is not
    such a map, raised ValueError
    """
    qubit_map = []

    # make coupling map bidirectional so we can find all neighbors
    cm = copy.deepcopy(topology_graph)
    for edge in topology_graph.edge_list():
        cm.add_edge(edge[1], edge[0], None)

    for starting_qubit in range(total_qubits):
        if starting_qubit not in faulty_qubits:
            qubit_map = [starting_qubit]
            new_neighbors = []
            prospective_neighbors = list(cm.neighbors(starting_qubit))
            while prospective_neighbors:
                for pn in prospective_neighbors:
                    if pn not in qubit_map and pn not in faulty_qubits:
                        new_neighbors.append(pn)
                qubit_map = qubit_map + new_neighbors
                prospective_neighbors = []
                for nn in new_neighbors:
                    potential_neighbors = list(cm.neighbors(nn))
                    for pn in potential_neighbors:
                        if pn not in prospective_neighbors:
                            prospective_neighbors.append(pn)
                new_neighbors = []
                if len(qubit_map) >= width:
                    return qubit_map[:width]
    raise ValueError("Insufficient connected qubits to create set of %d qubits", width)


# adapted from submodules/qiskit-device-benchmarking/qiskit_device_benchmarking/clops/clops_benchmark.py::prepare_clops_circuits
# As opposed to the original version of this function, this takes a topology graph as an argument instead of an IBM's coupling map object.
def append_2q_layer(
    qc: QuantumCircuit, topology_graph: rx.PyGraph, basis_gates: list[str], rng
) -> None:
    """
    Add a layer of random 2q gates.
    """
    available_edges = set(topology_graph.edge_list())
    while len(available_edges) > 0:
        edge = tuple(rng.choice(list(available_edges)))
        available_edges.remove(edge)
        edges_to_delete = []
        for ce in list(available_edges):
            if (edge[0] in ce) or (edge[1] in ce):
                edges_to_delete.append(ce)
        available_edges.difference_update(set(edges_to_delete))
        if "ecr" in basis_gates:
            qc.ecr(*edge)
        elif "cz" in basis_gates:
            qc.cz(*edge)
        else:
            qc.cx(*edge)
    return


# adapted from submodules/qiskit-device-benchmarking/qiskit_device_benchmarking/clops/clops_benchmark.py::prepare_clops_circuits
def prepare_clops_circuits(
    width: int,
    layers: int,
    num_circuits: int,
    basis_gates,
    topology_graph: rx.PyGraph,
    total_qubits: Optional[int],
    seed: int = 0,
) -> list[QuantumCircuit]:
    qubit_map = create_qubit_map(width, topology_graph, faulty_qubits=[], total_qubits=total_qubits)

    for edge in topology_graph.edge_list():
        if edge[0] not in qubit_map or edge[1] not in qubit_map:
            topology_graph.remove_edge(*edge)

    qc = QuantumCircuit(max(qubit_map) + 1, max(qubit_map) + 1)
    qubits = [qc.qubits[i] for i in qubit_map]

    parameters = []
    rng = np.random.default_rng(seed)
    for d in range(layers):
        append_2q_layer(qc, topology_graph, basis_gates, rng)
        parameters += append_1q_layer(qc, qubits, parameterized=True, parameter_prefix="L" + str(d))

    for idx in range(width):
        qc.measure(qubit_map[idx], idx)

    # Parameters are instantiated for each circuit with random values
    parametrized_circuits = [
        qc.assign_parameters(
            [rng.uniform(0, np.pi * 2) for _ in range(sum([len(param) for param in parameters]))]
        )
        for _ in range(num_circuits)
    ]

    return parametrized_circuits


class Clops(Benchmark):
    def dispatch_handler(self, device: QuantumDevice) -> ClopsData:
        topology_graph = device_topology(device)
        circuits = prepare_clops_circuits(
            width=self.params.width,
            layers=self.params.num_layers,
            num_circuits=self.params.num_circuits,
            basis_gates=device.profile.basis_gates,
            topology_graph=topology_graph,
            total_qubits=device.num_qubits,
        )
        quantum_job: QuantumJob | list[QuantumJob] = device.run(circuits, shots=self.params.shots)
        provider_job_ids = flatten_job_ids(quantum_job)
        return ClopsData(
            provider_job_ids=provider_job_ids,
        )

    def poll_handler(
        self,
        job_data: BenchmarkData,
        result_data: list[GateModelResultData],
        quantum_jobs: list[QuantumJob],
    ) -> ClopsResult:
        if not isinstance(job_data, ClopsData):
            raise TypeError(f"Expected job_data to be of type {type(ClopsData)}")
        clops_score = (self.params.num_layers * self.params.shots * self.params.num_circuits) / sum(
            execution_time(quantum_job) for quantum_job in quantum_jobs
        )
        return ClopsResult(clops_score=clops_score)
