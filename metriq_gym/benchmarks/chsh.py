"""CHSH benchmark for the Metriq Gym (credit to Paul Nation for the original code for IBM devices).

The CHSH benchmark evaluates a quantum device's ability to produce entangled states and measure correlations that
violate the CHSH inequality. The violation of this inequality indicates successful entanglement between qubits.
"""

from dataclasses import dataclass
import networkx as nx
import numpy as np
from qbraid import QuantumDevice, ResultData
from qbraid.runtime.result_data import MeasCount
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


@dataclass
class CHSHData(BenchmarkData):
    shots: int


class GraphColoring:
    """A simple class containing graph coloring data."""

    def __init__(self, num_nodes, edge_color_map, edge_index_map):
        self.edge_color_map = edge_color_map
        self.edge_index_map = edge_index_map
        self.num_colors = max(edge_color_map.values()) + 1
        self.num_nodes = num_nodes


def device_coloring(device: QuantumDevice) -> GraphColoring:
    """Graph coloring for a device's topology.

    Parameters:
        device: The qBraid device.

    Returns:
        GraphColoring: Coloring object
    """
    if isinstance(device, IonQDevice):
        # Complete graph for IonQ devices
        topology_graph = nx.complete_graph(device.num_qubits)
        edge_color_map = {i: 0 for i in range(topology_graph.number_of_edges())}
        topology_graph = rx.networkx_converter(topology_graph)
    elif isinstance(device, QiskitBackend):
        # Get the graph of the coupling map
        topology_graph = device._backend.coupling_map.graph
        # Got to undirected graph for coloring
        undirected_graph = topology_graph.to_undirected(multigraph=False)
        # Graphs are bipartite so use that feature to prevent extra colors from greedy search
        edge_color_map = rx.graph_bipartite_edge_color(undirected_graph)
        topology_graph = undirected_graph
    elif isinstance(device, BraketDevice):
        topology_graph = nx.Graph(device._device.topology_graph)
        raise ValueError("Braket devices are still being worked on (UF).")
    else:
        raise ValueError("Unsupported device type.")

    # Get the index of the edges
    edge_index_map = topology_graph.edge_index_map()
    return GraphColoring(device.num_qubits, edge_color_map, edge_index_map)


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


def chsh_subgraph_ionq(jobs, num_qubits):
    """Return subgraph where all edges correspond to qubit
    pairs that violate the CHSH inequality for IonQ.

    Parameters:
        jobs (list): A list of jobs to process.
        num_qubits (int): Number of qubits in the device.

    Returns:
        rx.PyGraph: Graph for the CHSH subgraph.
    """
    good_edges = []
    for job_idx, job in enumerate(jobs):
        print(job_idx, len(jobs))
        counts_list = [result.data.c.get_counts() for result in job.result()]

        for idx, counts in enumerate(counts_list):
            print(idx, counts)
            num_meas_pairs = len(counts.keys()) // 2  # Each measurement pair contributes two keys
            exp_vals = np.zeros(num_meas_pairs, dtype=float)
            for pair in range(num_meas_pairs):
                print(pair, len(counts_list))
                sub_counts = marginal_counts(counts, [2 * pair, 2 * pair + 1])
                exp_val = sampled_expectation_value(sub_counts, "ZZ")
                exp_vals[pair] += exp_val if idx != 2 else -exp_val

            for pair_idx, exp_val in enumerate(exp_vals):
                print(pair_idx, exp_val, len(exp_vals))
                # Convert pair index back to qubit pair
                edge = (pair_idx // num_qubits, pair_idx % num_qubits)
                if exp_val > 2:  # CHSH inequality violation
                    good_edges.append(edge)

    # Create the good subgraph
    good_graph = rx.PyGraph(multigraph=False)
    good_graph.add_nodes_from(list(range(num_qubits)))
    for edge in good_edges:
        good_graph.add_edge(*edge, 1)
    return good_graph


def largest_connected_size(good_graph):
    cc = rx.connected_components(good_graph)
    largest_cc = cc[np.argmax([len(g) for g in cc])]
    return len(largest_cc)


def generate_chsh_circuits_ionq(
    topology_graph, sample_edges: int | None = None
) -> list[QuantumCircuit]:
    """Generate CHSH circuits for IonQ's complete graph topology.

    Parameters:
        topology_graph (rx.PyGraph): Complete graph representing the IonQ topology.
        sample_edges (int): Optional. Number of edges to sample from the complete graph.
                            If None, use all edges.

    Returns:
        list[QuantumCircuit]: List of QuantumCircuit objects for the CHSH experiment.
    """
    num_qubits = topology_graph.number_of_nodes()
    circuits = []

    # Convert edges to a list of tuples
    all_edges = list(topology_graph.edges())

    # If sampling is required
    if sample_edges:
        sampled_indices = np.random.choice(len(all_edges), size=sample_edges, replace=False)
        edges = [all_edges[i] for i in sampled_indices]
    else:
        edges = all_edges

    for edge in edges:
        # Each edge generates 4 circuits (one for each CHSH basis)
        qubit_pair = edge[:2]  # Extract the pair of qubits
        for basis in ["ZZ", "ZX", "XZ", "XX"]:
            # Initialize a circuit for this edge and basis
            qc = QuantumCircuit(num_qubits, 2)

            # Prepare the Bell state
            qc.h(qubit_pair[0])
            qc.cx(*qubit_pair)

            # Apply rotation on one qubit
            qc.ry(np.pi / 4, qubit_pair[0])

            # Basis-dependent rotations
            if basis[0] == "X":
                qc.h(qubit_pair[0])
            if basis[1] == "X":
                qc.h(qubit_pair[1])

            # Add measurements
            qc.measure(qubit_pair[0], 0)
            qc.measure(qubit_pair[1], 1)

            # Add the circuit to the list
            circuits.append(qc)

    return circuits


class CHSH(Benchmark):
    def dispatch_handler(self, device: QuantumDevice) -> CHSHData:
        shots = self.params.shots

        if isinstance(device, IonQDevice):
            provider_backend = device
            topology_graph = nx.complete_graph(device.num_qubits)
            trans_exp_sets = generate_chsh_circuits_ionq(topology_graph, sample_edges=5)
        elif isinstance(device, QiskitBackend):
            provider_backend = device._backend
            coloring = device_coloring(device)
            exp_sets = generate_chsh_circuit_sets(coloring)

            pm = generate_preset_pass_manager(1, provider_backend)
            trans_exp_sets = [pm.run(circ_set) for circ_set in exp_sets]

        quantum_jobs = []
        print(len(trans_exp_sets))
        for i, circ_set in enumerate(trans_exp_sets):
            print(i)
            quantum_jobs.append(device.run(circ_set, shots=shots))

        # quantum_jobs: list[QuantumJob] = [
        #     device.run(circ_set, shots=shots) for circ_set in trans_exp_sets
        # ]

        provider_job_ids = [
            job.id
            for quantum_job_set in quantum_jobs
            for job in (quantum_job_set if isinstance(quantum_job_set, list) else [quantum_job_set])
        ]
        good_graph = chsh_subgraph_ionq(quantum_jobs, device.num_qubits)
        largest_size = largest_connected_size(good_graph)
        print(largest_size)
        return CHSHData(
            provider_job_ids=provider_job_ids,
            shots=shots,
        )

    def poll_handler(self, job_data: BenchmarkData, result_data: list[ResultData]) -> None:
        if not isinstance(job_data, CHSHData):
            raise TypeError(f"Expected job_data to be of type {type(CHSHData)}")

        print(result_data)
        counts: list[MeasCount]  # one MeasCount per trial

        # AWS vs IBM
        if len(result_data) == 1:
            counts = result_data[0].get_counts()
        else:
            counts = [r.get_counts() for r in result_data]
        print(counts)

        # counts: list[MeasCount]  # one MeasCount per trial
        # exit()
        # good_graph = chsh_subgraph(quantum_jobs, coloring)
        # largest_size = largest_connected_size(good_graph)
        # print(largest_size)

        # # AWS vs IBM
        # if len(result_data) == 1:
        #     counts = result_data[0].get_counts()
        # else:
        #     counts = [r.get_counts() for r in result_data]
