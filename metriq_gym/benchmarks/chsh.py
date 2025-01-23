"""CHSH benchmark for the Metriq Gym (credit to Paul Nation for the original code for IBM devices)."""

from dataclasses import dataclass
import numpy as np
import rustworkx as rx

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import Batch, SamplerV2
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
from qiskit.result import marginal_counts, sampled_expectation_value

from metriq_gym.benchmarks.benchmark import BenchmarkData


@dataclass
class CHSHData(BenchmarkData):
    num_qubits: int
    shots: int
    depth: int
    confidence_level: float
    ideal_probs: list[list[float]]
    trials: int


class GraphColoring:
    """A simple class containing graph coloring data."""

    def __init__(self, num_nodes, edge_color_map, edge_index_map):
        self.edge_color_map = edge_color_map
        self.edge_index_map = edge_index_map
        self.num_colors = max(edge_color_map.values()) + 1
        self.num_nodes = num_nodes


def backend_coloring(backend):
    """Graph coloring for a backend entangling gate topology.

    Parameters:
        backend (IBMBackend): Target backend to be colored

    Returns:
        GraphColoring: Coloring object
    """
    # Get the graph of the coupling map
    graph = backend.coupling_map.graph
    # Got to undirected graph for coloring
    undirected_graph = graph.to_undirected(multigraph=False)
    # Graphs are bipartite so use that feature to prevent extra colors from greedy search
    edge_color_map = rx.graph_bipartite_edge_color(undirected_graph)
    # Get the index of the edges
    edge_index_map = undirected_graph.edge_index_map()
    return GraphColoring(graph.num_nodes(), edge_color_map, edge_index_map)


def generate_chsh_circuit_sets(coloring):
    """Generate CHSH circuits from a coloring

    Parameters:
        coloring (GraphColoring): Coloring from a backend

    Returns:
        list: Nested list of QuantumCircuit objects
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
            qc.ry(np.pi / 4, edge[0])
        circuits.append(qc)

    exp_sets = []
    # For each coloring circuit, generate 4 new circuits with the required post-rotation operators
    # and measurements appended
    for counter, circ in enumerate(circuits):
        meas_circuits = []
        # Need to create a circuit for each measurement basis.  This amounts to appending
        # a H gate to the qubits with an X-basis measurement
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


def chsh_subgraph(jobs, coloring):
    """Return subgraph where all edges correspond to qubit
    pairs that violate the CHSH inequality

    Parameters:
        jobs (list): A list of jobs to process
        coloring (GraphColoring): The backend coloring

    Returns:
        PyGraph: Graph for the CHSH subgraph
    """
    good_edges = []
    for job_idx, job in enumerate(jobs):
        num_meas_pairs = len(
            {key for key, val in coloring.edge_color_map.items() if val == job_idx}
        )
        exp_vals = np.zeros(num_meas_pairs, dtype=float)
        for idx in range(4):
            counts = job.result()[idx].data.c.get_counts()
            for pair in range(num_meas_pairs):
                sub_counts = marginal_counts(counts, [2 * pair, 2 * pair + 1])
                exp_val = sampled_expectation_value(sub_counts, "ZZ")
                exp_vals[pair] += exp_val if idx != 2 else -exp_val
        for idx, edge_idx in enumerate(
            key for key, val in coloring.edge_color_map.items() if val == job_idx
        ):
            edge = (coloring.edge_index_map[edge_idx][0], coloring.edge_index_map[edge_idx][1])
            if exp_vals[idx] > 2:
                good_edges.append(edge)
    good_graph = rx.PyGraph(multigraph=False)
    good_graph.add_nodes_from(list(range(coloring.num_nodes)))
    for edge in good_edges:
        good_graph.add_edge(*edge, 1)
    return good_graph


def largest_connected_size(good_graph):
    cc = rx.connected_components(good_graph)
    largest_cc = cc[np.argmax([len(g) for g in cc])]
    return len(largest_cc)


# service = QiskitRuntimeService()
# backend = service.backend("ibm_sherbrooke")
# backend = GenericBackendV2(num_qubits=127)
# backend = AerSimulator.from_backend(service.backend("ibm_sherbrooke"))
backend = FakeManilaV2()
coloring = backend_coloring(backend)
exp_sets = generate_chsh_circuit_sets(coloring)

pm = generate_preset_pass_manager(1, backend)
trans_exp_sets = [pm.run(circ_set) for circ_set in exp_sets]
batch = Batch(backend=backend)
sampler = SamplerV2(mode=batch)
jobs = [sampler.run(circ_set, shots=512) for circ_set in trans_exp_sets]
good_graph = chsh_subgraph(jobs, coloring)
largest_size = largest_connected_size(good_graph)

print(largest_size / coloring.num_nodes)
