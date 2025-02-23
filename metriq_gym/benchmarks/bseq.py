""" "Bell state effective qubits" BSEQ benchmark for the Metriq Gym
(credit to Paul Nation for the original code for IBM devices).

This benchmark evaluates a quantum device's ability to produce entangled states and measure correlations that violate
the CHSH inequality. The violation of this inequality indicates successful entanglement between qubits.
"""

from dataclasses import dataclass, field

import networkx as nx
import rustworkx as rx
import numpy as np
from qbraid import GateModelResultData, QuantumDevice, QuantumJob, ResultData
from qbraid.runtime import (
    BraketDevice,
    QiskitBackend,
)

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.result import marginal_counts, sampled_expectation_value

from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkData


def _convert_rustworkx_to_networkx(graph: rx.PyGraph) -> nx.Graph:
    """Convert a rustworkx PyGraph or PyDiGraph to a networkx graph.

    Adapted from:
    https://www.rustworkx.org/dev/networkx.html#converting-from-a-networkx-graph
    """
    edge_list = [(graph[x[0]], graph[x[1]], {"weight": x[2]}) for x in graph.weighted_edge_list()]
    graph_type = (
        nx.MultiGraph
        if graph.multigraph
        else nx.Graph
        if isinstance(graph, rx.PyGraph)
        else nx.MultiDiGraph
        if graph.multigraph
        else nx.DiGraph
    )
    return graph_type(edge_list)


@dataclass
class GraphColoring:
    """A simple class containing graph coloring data.

    Attributes:
        num_nodes: Number of qubits (nodes) in the graph.
        edge_color_map: Maps each edge index to a color (integer).
        edge_index_map: Maps edge indices to actual qubit pairs.
        num_colors: Total number of colors assigned in the graph.
    """

    num_nodes: int
    edge_color_map: dict
    edge_index_map: dict
    num_colors: int = field(init=False)

    def __post_init__(self):
        self.num_colors = max(self.edge_color_map.values()) + 1

    @classmethod
    def from_dict(cls, data: dict) -> "GraphColoring":
        """Reconstruct GraphColoring from a dictionary, ensuring integer keys."""
        return cls(
            num_nodes=data["num_nodes"],
            edge_color_map={int(k): v for k, v in data["edge_color_map"].items()},
            edge_index_map={int(k): v for k, v in data["edge_index_map"].items()},
        )


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


def device_graph_coloring(topology_graph: rx.PyGraph) -> GraphColoring:
    """Performs graph coloring for a quantum device's topology.

    The goal is to assign colors to edges such that no two adjacent edges have the same color.
    This ensures independent BSEQ experiments can be run in parallel. Identifies qubit pairs (edges)
    that can be executed without interference. These pairs are grouped by "color." The coloring reduces
    the complexity of the benchmarking process by organizing the graph into independent sets of qubit pairs.

    Args:
        topology_graph: The topology graph (coupling map) of the quantum device.

    Returns:
        GraphColoring: An object containing the coloring information.
    """
    num_nodes = _convert_rustworkx_to_networkx(topology_graph).number_of_nodes()
    # Graphs are bipartite, so use that feature to prevent extra colors from greedy search.
    # This graph is colored using a bipartite edge-coloring algorithm.
    edge_color_map = rx.graph_bipartite_edge_color(topology_graph)

    # Get the index of the edges.
    edge_index_map = dict(topology_graph.edge_index_map())
    return GraphColoring(
        num_nodes=num_nodes, edge_color_map=edge_color_map, edge_index_map=edge_index_map
    )


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


def chsh_subgraph(coloring: GraphColoring, result_data: list[GateModelResultData]) -> rx.PyGraph:
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
    for job_idx, result in enumerate(result_data):
        if result.measurement_counts is None:
            continue
        num_meas_pairs = len(
            {key for key, val in coloring.edge_color_map.items() if val == job_idx}
        )
        exp_vals: np.ndarray = np.zeros(num_meas_pairs, dtype=float)

        # IBM case: multiple dictionaries (one per measurement basis)
        if isinstance(result.measurement_counts, list):
            for idx in range(4):
                counts = result.measurement_counts[idx]
                for pair in range(num_meas_pairs):
                    sub_counts = marginal_counts(counts, [2 * pair, 2 * pair + 1])
                    exp_val = sampled_expectation_value(sub_counts, "ZZ")
                    exp_vals[pair] += exp_val if idx != 2 else -exp_val

        # AWS case: single dictionary → Simulate different measurement bases
        elif isinstance(result.measurement_counts, dict):
            counts = result.measurement_counts
            # TODO: Something needs to actually happen here but at present I don't know how or what.

        for idx, edge_idx in enumerate(
            key for key, val in coloring.edge_color_map.items() if val == job_idx
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


def largest_connected_size(good_graph: rx.PyGraph) -> int:
    """Finds the size of the largest connected component in the CHSH subgraph.

    Args:
        good_graph: The graph of qubit pairs that violated CHSH inequality.

    Returns:
        The size of the largest connected component.
    """
    cc = rx.connected_components(good_graph)
    largest_cc = cc[np.argmax([len(g) for g in cc])]
    return len(largest_cc)


class BSEQ(Benchmark):
    """Benchmark class for BSEQ (Bell state effective qubits) experiments."""

    def dispatch_handler(self, device: QuantumDevice) -> BSEQData:
        """Runs the benchmark and returns job metadata."""
        shots = self.params.shots
        trans_exp_sets: list[list[QuantumCircuit]]

        if isinstance(device, QiskitBackend):
            topology_graph = device._backend.coupling_map.graph.to_undirected(multigraph=False)

            coloring = device_graph_coloring(topology_graph)
            exp_sets = generate_chsh_circuit_sets(coloring)

            pm = generate_preset_pass_manager(1, device._backend)
            trans_exp_sets = [pm.run(circ_set) for circ_set in exp_sets]

        elif isinstance(device, BraketDevice):
            topology_graph = rx.networkx_converter(nx.Graph(device._device.topology_graph))
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

    def poll_handler(self, job_data: BenchmarkData, result_data: list[ResultData]) -> None:
        """Poll and calculate largest connected component."""
        if not isinstance(job_data, BSEQData):
            raise TypeError(f"Expected job_data to be of type {type(BSEQData)}")

        if job_data.coloring:
            if isinstance(job_data.coloring, dict):
                job_data.coloring = GraphColoring.from_dict(job_data.coloring)
            good_graph = chsh_subgraph(job_data.coloring, result_data)
            print(f"Largest connected size: {largest_connected_size(good_graph)}")
