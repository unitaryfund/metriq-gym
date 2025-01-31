"""CHSH benchmark for the Metriq Gym (credit to Paul Nation for the original code for IBM devices).

The CHSH benchmark evaluates a quantum device's ability to produce entangled states and measure correlations that
violate the CHSH inequality. The violation of this inequality indicates successful entanglement between qubits.
"""

from dataclasses import dataclass
import networkx as nx
import numpy as np
from qbraid import QuantumDevice, QuantumJob, ResultData
from qbraid.runtime import (
    QiskitBackend,
    BraketDevice,
    IonQDevice,
)
import rustworkx as rx

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.result import marginal_counts, sampled_expectation_value

from metriq_gym.benchmarks.benchmark import Benchmark, BenchmarkData


class GraphColoring:
    """A simple class containing graph coloring data.

    Attributes:
        num_nodes: Number of qubits (nodes) in the graph.
        edge_color_map: Maps each edge index to a color (integer).
        edge_index_map: Maps edge indices to actual qubit pairs.
        num_colors: Total number of colors assigned in the graph.
    """

    def __init__(self, num_nodes: int, edge_color_map: dict, edge_index_map: dict) -> None:
        self.edge_color_map = edge_color_map
        self.edge_index_map = edge_index_map
        self.num_colors = max(edge_color_map.values()) + 1
        self.num_nodes = num_nodes


@dataclass
class CHSHData(BenchmarkData):
    """Data class to store CHSH benchmark metadata.

    Attributes:
        shots: Number of shots per quantum circuit execution.
        num_qubits: Number of qubits in the quantum device.
        topology_graph: Graph representing the device topology (optional).
        coloring: Coloring information for circuit partitioning (optional).
    """

    shots: int
    num_qubits: int
    topology_graph: nx.Graph | None = None
    coloring: GraphColoring | None = None


def ibm_device_coloring(device: QuantumDevice) -> GraphColoring:
    """Performs graph coloring for a quantum device's topology.

    The goal is to assign colors to edges such that no two adjacent edges have the same color.
    This ensures independent CHSH experiments can be run in parallel. Identifies qubit pairs (edges)
    that can be executed without interference. These pairs are grouped by "color." The coloring reduces
    the complexity of the benchmarking process by organizing the graph into independent sets of qubit pairs.

    Args:
        device: The quantum device.

    Returns:
        GraphColoring: An object containing the coloring information.
    """
    # Get the graph of the coupling map.
    topology_graph = device._backend.coupling_map.graph
    # Convert to undirected graph for coloring.
    undirected_graph = topology_graph.to_undirected(multigraph=False)
    # Graphs are bipartite, so use that feature to prevent extra colors from greedy search.
    # This graph is colored using a bipartite edge-coloring algorithm.
    edge_color_map = rx.graph_bipartite_edge_color(undirected_graph)
    topology_graph = undirected_graph

    # Get the index of the edges.
    edge_index_map = topology_graph.edge_index_map()
    return GraphColoring(device.num_qubits, edge_color_map, edge_index_map)


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


def ibm_chsh_subgraph(coloring: GraphColoring, result_data: list[ResultData]) -> rx.PyGraph:
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
        num_meas_pairs = len(
            {key for key, val in coloring.edge_color_map.items() if val == job_idx}
        )
        exp_vals = np.zeros(num_meas_pairs, dtype=float)
        for idx in range(4):
            counts = result.measurement_counts[idx]
            # Expectation values for the CHSH correlation terms are calculated based on measurement outcomes.
            for pair in range(num_meas_pairs):
                sub_counts = marginal_counts(counts, [2 * pair, 2 * pair + 1])
                exp_val = sampled_expectation_value(sub_counts, "ZZ")
                exp_vals[pair] += exp_val if idx != 2 else -exp_val
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


class CHSH(Benchmark):
    """Benchmark class for CHSH experiments."""

    def dispatch_handler(self, device: QuantumDevice) -> CHSHData:
        """Runs the benchmark and returns job metadata."""
        shots = self.params.shots

        # Handle all device-specific logic here
        topology_graph = None
        coloring = None
        trans_exp_sets = None

        if isinstance(device, QiskitBackend):
            coloring = ibm_device_coloring(device)
            exp_sets = generate_chsh_circuit_sets(coloring)
            pm = generate_preset_pass_manager(1, device._backend)
            trans_exp_sets = [pm.run(circ_set) for circ_set in exp_sets]

        elif isinstance(device, IonQDevice):
            topology_graph = nx.complete_graph(device.num_qubits)
            raise ValueError("IonQ devices are not supported at this time.")

        elif isinstance(device, BraketDevice):
            topology_graph = device._device.topology_graph
            raise ValueError("AWS devices are not supported at this time.")

        else:
            raise ValueError(f"Unsupported device type: {type(device)}")

        quantum_jobs: list[QuantumJob] = [
            device.run(circ_set, shots=shots) for circ_set in trans_exp_sets
        ]

        provider_job_ids = [job.id for job_set in quantum_jobs for job in job_set]

        return CHSHData(
            provider_job_ids=provider_job_ids,
            shots=shots,
            num_qubits=device.num_qubits,
            topology_graph=topology_graph,
            coloring=coloring,
        )

    def poll_handler(self, job_data: BenchmarkData, result_data: list[ResultData]) -> None:
        """Poll and calculate largest connected componenet."""
        if not isinstance(job_data, CHSHData):
            raise TypeError(f"Expected job_data to be of type {type(CHSHData)}")

        if job_data.coloring:
            good_graph = ibm_chsh_subgraph(job_data.coloring, result_data)
            print(f"Largest connected size: {largest_connected_size(good_graph)}")
