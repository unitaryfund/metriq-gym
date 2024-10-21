# From https://github.com/qiskit-community/qiskit-device-benchmarking/blob/b3861e1e71684d482d197a31b9c6dca17f2b5cc0/qiskit_device_benchmarking/clops/clops_benchmark.py

# (C) Copyright IBM 2024.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals


import copy
from functools import lru_cache
from typing import Callable, List, Optional, Sequence

import numpy as np
from qiskit import transpile
from qiskit.circuit import Barrier, Delay, ParameterVector, QuantumCircuit, Qubit
from qiskit.circuit.library import IGate, RZGate, SXGate, UGate
from qiskit_ibm_runtime import QiskitRuntimeService, Session
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit_ibm_runtime import SamplerOptions
from qiskit_ibm_runtime.options import TwirlingOptions
from qiskit_ibm_runtime.ibm_backend import Backend
from qiskit_ibm_runtime.execution_span import ExecutionSpan, ExecutionSpans

"""
CLOPS benchmark

This benchmark measures Circuit Layer Operations Per Seconds (CLOPS) of
parameterized utility scale  hardware efficient circuits.  CLOPS measures 
the steady state throughput of a large quantity of  these parameterized 
circuits that are  of width 100 qubits with 100 layers of gates. 
Each layer consists of two qubit gates across as many qubits
as possible that can be done in parallel, followed by a single qubit
gate(s) on every qubit to allow any arbitrary rotation, with those 
rotations being parameterized.  Parameters are applied to the circuit 
to generate a large number of  instantiated circuits to be executed on 
the quantum computer. It is up to the vendor on how to optimally execute 
these circuits for maximal throughput.  As such, the benchmark code 
provides several ways to measure CLOPS depending on the capability of 
the quantum computer. 

The "twirling" method uses the native parameterization of the Sampler
primitive to parameterize the circuit, and optimal batching of the 
circuits is assumed to be done by the Sampler, freeing the user
from having to optimize the batch size. The only requirement is
that the total number of circuits executed needs to be chosen to
get the system into a steady state to measure CLOPS.
The "parameterized" method is similar, but instead sends an already
parameterized circuit to the Sampler primitive, along with enough 
parameters to execute the specified number of circuits. Batching 
again is handled by the Sampler. This method requires larger bandwidth
to send in all of the necessary parameters.

The "instantiated" method is for systems that cannot natively 
handle parameterized circuits. In this case the circuit parameters
are bound locally and then sent to the quantum computer for execution.
This method requires the user to specify the desired size of each
batch of circuits (so that they can be sent together the quantum computer) 
as well as the number of local parallel pipelines to bind parameters and
create payloads in parallel. The user will need to tune both of these
parameters to try and optimize performance of the system. This will 
tend to be much slower than on systems that natively support parameterized
circuits

For further information see the clops_benchmark class
"""




"""
Functions for working with circuits of parameterized 1-qubit gates.
"""


def append_1q_layer(
    circuit: QuantumCircuit,
    qubits: Optional[Sequence[Qubit]] = None,
    basis: str = "rzsx",
    parameterized: bool = False,
    parameter_prefix: str = "θ",
) -> List[ParameterVector]:
    """Append a layer of 1-qubit gates on specified qubits with optional parameters

    Args:
        circuit: The circuit to append the layer to
        qubits: Optional, the qubits to add parameterized gates to.
                If None all qubits will be included.
        basis: The parameter basis for the parameterized gates.
        parameterized: If the gates are to be parameterized or fixed
        parameter_prefix: The prefix for the parameter vectors.

    Returns:
        The ordered list of ParameterVectors for the appended layer.
    """
    if qubits is None:
        qubits = circuit.qubits
    return _layer_basis_function(basis)(circuit, qubits, parameterized, parameter_prefix)


def _append_1q_layer_u(
    circuit, qubits: Sequence[Qubit], parameterized=True, param_prefix="θ"
) -> List[ParameterVector]:
    """Append a layer of parameterized 1-qubit gates on specified qubits."""
    size = len(qubits)
    pars0 = ParameterVector(f"{param_prefix}_0", size)
    pars1 = ParameterVector(f"{param_prefix}_1", size)
    pars2 = ParameterVector(f"{param_prefix}_2", size)

    for i, q in enumerate(qubits):
        if parameterized: 
            circuit._append(UGate(pars0[i], pars1[i], pars2[i]), [q], [])
        else:
            circuit._append(UGate(1.0, -3.14/2, 3.14/2), [q], [])

    return pars0, pars1, pars2


def _append_1q_layer_rzsx(
    circuit, qubits: List[Qubit], parameterized, param_prefix="θ"
) -> List[ParameterVector]:
    """Append a layer of parameterized 1-qubit gates on specified qubits."""
    size = len(qubits)
    pars0 = ParameterVector(f"{param_prefix}_0", size)
    pars1 = ParameterVector(f"{param_prefix}_1", size)
    pars2 = ParameterVector(f"{param_prefix}_2", size)

    for i, q in enumerate(qubits):
        if parameterized: 
            circuit._append(RZGate(pars0[i]), [q], [])
            circuit._append(SXGate(), [q], [])
            circuit._append(RZGate(pars1[i]), [q], [])
            circuit._append(SXGate(), [q], [])
            circuit._append(RZGate(pars2[i]), [q], [])
        else:
            circuit._append(SXGate(), [q], [])

    return pars0, pars1, pars2


def _append_1q_layer_pauli(
    circuit: QuantumCircuit, qubits: List[Qubit], parameterized, param_prefix="θ"
) -> List[ParameterVector]:
    """Append a layer of parameterized 1-qubit gates on specified qubits."""
    from pec_runtime.circuit.pauli_gate import PauliGate

    size = len(qubits)
    pars_z = ParameterVector(f"{param_prefix}_0", size)
    pars_x = ParameterVector(f"{param_prefix}_1", size)

    # As a work around for terra bug 8692 we apply 1-qubit PauliGates only
    # https://github.com/Qiskit/qiskit-terra/issues/8692
    # TODO: support non-parameterized if needed
    for qubit, pz, px in zip(qubits, pars_z, pars_x):
        circuit._append(PauliGate([pz], [px]), [qubit], [])
    return pars_z, pars_x


@lru_cache()
def _layer_basis_function(basis: str) -> Callable:
    """Return function for appending a parameterized layer"""
    _funcs = {
        "rzsx": _append_1q_layer_rzsx,
        "clifford": _append_1q_layer_rzsx,
        "u": _append_1q_layer_u,
        "pauli": _append_1q_layer_pauli,
    }
    if basis not in _funcs:
        raise ValueError(f"Invalid 1-qubit parameter basis {basis}")
    return _funcs[basis]


@lru_cache()
def _is_identity(cls) -> bool:
    """Return True if a gate class can be treated as identity."""
    if issubclass(cls, (IGate, Delay, Barrier)):
        return True
    return False


def create_qubit_map(width, coupling_map, faulty_qubits, total_qubits):
    """
    Returns a list of  'width' qubits that are connected based on a coupling map that has
    bad edges already removed and a list of faulty qubits.  If there is not
    such a map, raised ValueError
    """
    qubit_map = []

    # make coupling map bidirectional so we can find all neighbors
    cm = copy.deepcopy(coupling_map)
    for edge in list(cm):
        cm.add_edge(edge[1], edge[0])

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


def append_2q_layer(qc, coupling_map, basis_gates, rng):
    """
    Add a layer of random 2q gates.
    """
    available_edges = set(coupling_map)
    while len(available_edges) > 0:
        edge = tuple(rng.choice(list(available_edges)))
        available_edges.remove(edge)
        edges_to_delete = []
        for ce in list(available_edges):
            if (edge[0] in ce) or (edge[1] in ce):
                edges_to_delete.append(ce)
        available_edges.difference_update(set(edges_to_delete))
        if 'ecr' in basis_gates:
            qc.ecr(*edge)
        elif 'cz' in basis_gates:
            qc.cz(*edge)
        else:
            qc.cx(*edge)
    return


def create_hardware_aware_circuit(
    width: int, layers: int, backend, parameterized=True, rng=None
):
    """
    Creates a random circuit with a structure of alternating 1Q and 2Q gate layers.
    2Q gate layers respect the device coupling map.  1Q gate layers are parameterized
    if `parameterized` is set to True, otherwise returns fixed circuit.
    """
    if width < 1:
        raise ValueError("'width' must be at least 1")
    if layers < 1:
        raise ValueError("'layers' must be at least 1")
    config = backend.configuration()

    basis_gates = backend.configuration().basis_gates
    faulty_qubits = backend.properties().faulty_qubits()
    faulty_gates = backend.properties().faulty_gates()
    faulty_edges = [tuple(gate.qubits) for gate in faulty_gates if len(gate.qubits) > 1]
    coupling_map = copy.deepcopy(backend.coupling_map)
    # remove faulty_edges
    for edge in faulty_edges:
        if tuple(edge) in coupling_map:
            coupling_map.graph.remove_edge(edge[0], edge[1])
    qubit_map = create_qubit_map(width, coupling_map, faulty_qubits, config.num_qubits)

    # remove edges beyond the width of the circuit we are trying to generate
    for edge in coupling_map:
        if edge[0] not in qubit_map or edge[1] not in qubit_map:
            coupling_map.graph.remove_edge(*edge)

    qc = QuantumCircuit(max(qubit_map) + 1, max(qubit_map) + 1)

    qubits = [qc.qubits[i] for i in qubit_map]
    param_list = []
    seed = 234987
    rng = np.random.default_rng(seed)
    for d in range(layers):
        # add 2 qubit gate layer, layer_type indicates even, odd or cross row connections.
        append_2q_layer(qc, coupling_map, basis_gates, rng)

        # add single qubit gate layer with optional parameters
        param_list += append_1q_layer(
            qc, qubits=qubits, parameterized=parameterized, parameter_prefix="L" + str(d)
        )

    transpiled_circ = transpile(
        qc, backend, translation_method="translator", layout_method="trivial"
    )

    for idx in range(width):
        transpiled_circ.measure(qubit_map[idx], idx)

    return transpiled_circ, param_list


def create_payload(backend, qc, rng, max_experiments):
    """
    Creates a payload of instantiated parameterized circuits that maximizes
    throughput
    """
    if max_experiments is None:
        max_experiments = backend.configuration().max_experiments
    job = []

    for idx in range(max_experiments):
        val = {}
        for param in qc.parameters:
            val[param] = rng.uniform(0, np.pi * 2)
        job.append(qc.assign_parameters(val))
    return job, max_experiments



def run_twirled(
    backend: Backend, 
    width: int,
    layers: int,
    shots: int, 
    rep_delay: float,
    num_circuits: int,
):
    (transpiled_circ , _) = create_hardware_aware_circuit(width=width, layers=layers, backend=backend, parameterized=False)
    twirling_opts = TwirlingOptions(num_randomizations=num_circuits, shots_per_randomization=shots, enable_gates=True)
    experimental_opts = {"execution": {"fast_parametric_update": True}}
    options = SamplerOptions(twirling=twirling_opts, experimental=experimental_opts)

    with Session(backend=backend) as session:
        sampler=Sampler(mode=session, options=options)
        job = sampler.run([transpiled_circ], shots=shots*num_circuits)

    return job


def run_parameterized(
    backend: Backend, 
    width: int,
    layers: int,
    shots: int, 
    rep_delay: float,
    num_circuits: int,
):
    (transpiled_circ, parameters) = create_hardware_aware_circuit(width=width, layers=layers, backend=backend, parameterized=True)
    seed = 234987
    rng = np.random.default_rng(seed)
    
    param_values = [[rng.uniform(0, np.pi * 2) for idx in range(sum([len(param) for param in parameters]))] 
                     for idx in range(num_circuits)]
    
    experimental_opts = {"execution": {"fast_parametric_update": True}}
    options = SamplerOptions(experimental=experimental_opts)

    with Session(backend=backend) as session:
        sampler=Sampler(mode=session, options=options)
        job = sampler.run([(transpiled_circ, param_values , shots)])
    
    return job

class clops_benchmark:

    def __init__(self,
        service: QiskitRuntimeService,
        backend_name: str,
        width: int = 100,
        layers: int = 100,
        shots: int = 100,
        rep_delay: float = None,
        num_circuits: int = 1000,
        circuit_type: str = "twirled",
        batch_size: int = None,
        pipelines: int = 1,
    ):
        
        """Run CLOPS benchmark through Sampler primitive

        Args:
            service: instantiated service to use to run the benchmark
            backend_name: The backend to run the benchmark
            width: Optional, width of the CLOPS circuit, default is 100 qubits wide
            layers: Optional, number of layers in the CLOPS circuit, default is 100
                    which yields a 5K circuit when combined with 100 qubits wide
            shots: Optional, number of shots per circuit, default is 100
            rep_delay: Optional, delay between circuits, default is set to system value
            num_circuits: Optional, number of circuits (parameter updates) run for the benchmark
                          default is 1000.  Adjust as necessary to get sufficient iterations.
                          For non-twirled benchmarking may need to be significantly reduced to 
                          meet API input size limits
            circuit_type: Optional, determines how parameters are handled:
                        "twirled": default value, sends in a single unparameterized circuit and configures 
                                   Sampler to run `num_circuits` twirls (parameterized) of the circuit
                        "parameterized": sends in a single parameterized circuit with `num_circuits` parameter sets
                        "instantiated": binds parameters locally and sends batches of instantiated circuits to be run
            batch_size: Optional, indicates how many circuits should be sent in per job to the backend. Only used 
                        for `instantiated` circuit_type. Default is None
            pipelines: Optional, number of parallel processes used to instantiate parameters and submit jobs to
                    the backend. Only used for `instantiated` circuit_type.  Default is 1
        """

        #service = QiskitRuntimeService(channel="ibm_quantum")
        backend = service.backend(backend_name)
        if rep_delay is None:
            rep_delay = backend.configuration().default_rep_delay

        self.job_attributes = {"backend_name": backend_name, "width": width, "layers": layers, "shots": shots,
                               "rep_delay": rep_delay, "num_circuits": num_circuits, "circuit_type": circuit_type,
                               "batch_size": batch_size, "pipelines": pipelines}
        
        if circuit_type == "twirled":
            self.job = run_twirled(backend, width, layers, shots, rep_delay, num_circuits)
            self.clops = self._clops_throughput_sampler
        elif circuit_type == "parameterized":
            self.job = run_parameterized(backend, width, layers, shots, rep_delay, num_circuits)
            self.clops = self._clops_throughput_sampler
        elif circuit_type == "instantiated":
            raise ValueError("'circuit_type' instantiated not yet supported")
        else:
            raise ValueError("'circuit_type' " + circuit_type + " invalid")
        
        
    def _clops_throughput_sampler(self):
        """ Measures the overall CLOPS throughput based off of intermediate
        job metadata returned from the sampler. This metadata indicates the 
        start and end time for each sub-job executed on the qpu.  For larger
        jobs (large number of twirls or large number of circuits/parameters) 
        jobs are split into chunks that efficiently run on the qpu. To calculate
        the steady state throughput we use the time from the end of the first 
        sub-job to the end of the last sub-job, skipping the startup costs
        for the first job to get the pipeline full. The goal is to predict 
        the expected performance for large scale error mitigated workloads 
        without having to run huge number of circuits"""

        result = self.job.result()
        execution_spans: ExecutionSpans = result.metadata["execution"]["execution_spans"]
        spans = execution_spans.sort()
        span: ExecutionSpan
        sum_size: int = 0

        for span in spans:
            sum_size += span.size

        end_time_last_sub_job = spans.stop
        end_time_first_sub_job = spans[0].stop

        clops = round(((sum_size - spans[0].size) * self.job_attributes["layers"]) / 
                      (end_time_last_sub_job - end_time_first_sub_job
        ).total_seconds())

        return clops
