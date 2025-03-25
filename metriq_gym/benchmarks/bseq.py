""" "Bell state effective qubits" BSEQ benchmark for the Metriq Gym
(credit to Paul Nation for the original code for IBM devices).

This benchmark evaluates a quantum device's ability to produce entangled states and measure correlations that violate
the CHSH inequality. The violation of this inequality indicates successful entanglement between qubits.
"""

import os
from dataclasses import dataclass
from datetime import datetime

import networkx as nx
import rustworkx as rx
import numpy as np
from qbraid import GateModelResultData, QuantumDevice, QuantumJob
from qbraid.runtime.result_data import MeasCount

from qiskit import QuantumCircuit
from qiskit.result import marginal_counts, sampled_expectation_value

from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkData, BenchmarkResult
from metriq_gym.helpers.task_helpers import flatten_counts
from metriq_gym.helpers.graph_helpers import (
    GraphColoring,
    device_graph_coloring,
    largest_connected_size,
)
from metriq_gym.qplatform.device import connectivity_graph

from metriq_client import MetriqClient
from metriq_client.models import ResultCreateRequest


@dataclass
class BSEQResult(BenchmarkResult):
    largest_connected_size: int
    fraction_connected: float


@dataclass
class BSEQData(BenchmarkData):
    """Data class to store BSEQ benchmark metadata.

    Attributes:
        shots: Number of shots per quantum circuit execution.
        num_qubits: Number of qubits in the quantum device.
        topology_graph: Graph representing the device topology (optional).
        coloring: Coloring information for circuit partitioning (optional).
    """

    shots: int
    num_qubits: int
    topology_graph: nx.Graph | None = None
    coloring: GraphColoring | dict | None = None


def generate_chsh_circuit_sets(coloring: GraphColoring) -> list[QuantumCircuit]:
    """Generate CHSH circuits based on graph coloring.

    Args:
        coloring: The coloring information of the quantum device topology.

    Returns:
        Nested list of QuantumCircuit objects, grouped by color.
    """
    num_qubits = coloring.num_nodes
    circuits = []
    # For each coloring, generate a set of CHSH pairs (Bell pairs plus an Ry(pi/4)) on each
    # edge of the coloring.  Measurement register is twice the number of qubit pairs in the
    # coloring
    for counter in range(coloring.num_colors):
        num_qubit_pairs = len(
            {key for key, val in coloring.edge_color_map.items() if val == counter}
        )
        qc = QuantumCircuit(num_qubits, 2 * num_qubit_pairs)
        for edge_idx in (key for key, val in coloring.edge_color_map.items() if val == counter):
            edge = (coloring.edge_index_map[edge_idx][0], coloring.edge_index_map[edge_idx][1])
            # For each edge in the color set perform a CHSH experiment at the optimal value
            qc.h(edge[0])
            qc.cx(*edge)
            # Apply CHSH-specific rotation.
            qc.ry(np.pi / 4, edge[0])
        circuits.append(qc)

    exp_sets = []
    # For each coloring circuit, generate 4 new circuits with the required post-rotation operators
    # and measurements appended
    for counter, circ in enumerate(circuits):
        meas_circuits = []
        # Need to create a circuit for each measurement basis. This amounts to appending a H gate to the qubits with an
        # X-basis measurement Each basis corresponds to one of the four CHSH correlation terms.
        for basis in ["ZZ", "ZX", "XZ", "XX"]:
            temp_qc = circ.copy()
            meas_counter = 0
            for edge_idx in (key for key, val in coloring.edge_color_map.items() if val == counter):
                edge = (coloring.edge_index_map[edge_idx][0], coloring.edge_index_map[edge_idx][1])
                for idx, oper in enumerate(basis[::-1]):
                    if oper == "X":
                        temp_qc.h(edge[idx])
                temp_qc.measure(edge, [meas_counter, meas_counter + 1])
                meas_counter += 2
            meas_circuits.append(temp_qc)
        exp_sets.append(meas_circuits)

    return exp_sets


def chsh_subgraph(coloring: GraphColoring, counts: list[MeasCount]) -> rx.PyGraph:
    """Constructs a subgraph of qubit pairs that violate the CHSH inequality.

    Args:
        job_data: The benchmark metadata including topology and coloring.
        result_data: The result data containing measurement counts.

    Returns:
        The graph of edges that violated the CHSH inequality.
    """
    # A subgraph is constructed containing only the edges (qubit pairs) that successfully violate the CHSH inequality.
    # The size of the largest connected component in this subgraph provides a measure of the device's performance.
    good_edges = []
    for color_idx in range(coloring.num_colors):
        num_meas_pairs = len(
            {key for key, val in coloring.edge_color_map.items() if val == color_idx}
        )
        exp_vals: np.ndarray = np.zeros(num_meas_pairs, dtype=float)

        for idx in range(4):
            for pair in range(num_meas_pairs):
                sub_counts = marginal_counts(counts[color_idx * 4 + idx], [2 * pair, 2 * pair + 1])
                exp_val = sampled_expectation_value(sub_counts, "ZZ")
                exp_vals[pair] += exp_val if idx != 2 else -exp_val

        for idx, edge_idx in enumerate(
            key for key, val in coloring.edge_color_map.items() if val == color_idx
        ):
            edge = (coloring.edge_index_map[edge_idx][0], coloring.edge_index_map[edge_idx][1])
            # The benchmark checks whether the CHSH inequality is violated (i.e., the sum of correlations exceeds 2,
            # indicating entanglement).
            if exp_vals[idx] > 2:
                good_edges.append(edge)

    good_graph = rx.PyGraph(multigraph=False)
    good_graph.add_nodes_from(list(range(coloring.num_nodes)))
    for edge in good_edges:
        good_graph.add_edge(*edge, 1)
    return good_graph


class BSEQ(Benchmark):
    """Benchmark class for BSEQ (Bell state effective qubits) experiments."""

    def dispatch_handler(self, device: QuantumDevice) -> BSEQData:
        """Runs the benchmark and returns job metadata."""
        shots = self.params.shots

        topology_graph = connectivity_graph(device)
        coloring = device_graph_coloring(topology_graph)
        trans_exp_sets = generate_chsh_circuit_sets(coloring)

        quantum_jobs: list[QuantumJob | list[QuantumJob]] = [
            device.run(circ_set, shots=shots) for circ_set in trans_exp_sets
        ]

        provider_job_ids = [
            job.id
            for quantum_job_set in quantum_jobs
            for job in (quantum_job_set if isinstance(quantum_job_set, list) else [quantum_job_set])
        ]

        return BSEQData(
            provider_job_ids=provider_job_ids,
            shots=shots,
            num_qubits=device.num_qubits,
            topology_graph=topology_graph,
            coloring={
                "num_nodes": coloring.num_nodes,
                "edge_color_map": dict(coloring.edge_color_map),
                "edge_index_map": dict(coloring.edge_index_map),
            },
        )

    def poll_handler(
        self,
        job_data: BSEQData,
        result_data: list[GateModelResultData],
        quantum_jobs: list[QuantumJob],
    ) -> BSEQResult:
        """Poll and calculate largest connected component."""
        if not job_data.coloring:
            raise ValueError("Coloring data is required for BSEQ benchmark.")

        if isinstance(job_data.coloring, dict):
            job_data.coloring = GraphColoring.from_dict(job_data.coloring)
        good_graph = chsh_subgraph(job_data.coloring, flatten_counts(result_data))
        lcs = largest_connected_size(good_graph)
        return BSEQResult(
            largest_connected_size=lcs,
            fraction_connected=lcs / job_data.coloring.num_nodes,
        )

    def upload_handler(
        self, job_data: BenchmarkData, result_data: BenchmarkResult, dispatch_time: datetime, submission_id: int, platform_id: int,
    ) -> None:
        client = MetriqClient(os.environ.get("METRIQ_CLIENT_API_KEY"))
        task_id = 236 #BSEQ task ID
        method_id = 426 #BSEQ method ID
        client.submission_add_task(submission_id, task_id)
        client.submission_add_method(submission_id, method_id)
        client.submission_add_platform(submission_id, platform_id)
        result_create_request = ResultCreateRequest(
            task = str(task_id),
            method = str(method_id),
            platform = str(platform_id),
            isHigherBetter = str(True),
            metricName = "",
            metricValue = str(0),
            evaluatedAt = dispatch_time.strftime("%Y-%m-%d"),
            qubitCount = str(job_data.num_qubits),                                         # type: ignore[attr-defined]
            shots = str(job_data.shots),                                                   # type: ignore[attr-defined]
            # circuitDepth = str(job_data.num_qubits),
            # sampleSize = str(job_data.trials),
            # notes: str | None = None
            # standardError: str | None = None
        )
        result_create_request.metricName = "Largest connected component size"
        result_create_request.metricValue = str(result_data.largest_connected_size)    # type: ignore[attr-defined]
        client.result_add(result_create_request, submission_id)
        result_create_request.metricName = "Largest connected component size per node"
        result_create_request.metricValue = str(result_data.fraction_connected)        # type: ignore[attr-defined]
        client.result_add(result_create_request, submission_id)