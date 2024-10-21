# From https://github.com/qiskit-community/qiskit-device-benchmarking/blob/b3861e1e71684d482d197a31b9c6dca17f2b5cc0/qiskit_device_benchmarking/bench_code/bell/bell_experiment.py

# (C) Copyright IBM 2024.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals

from typing import List, Tuple, Sequence
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from qiskit.circuit import QuantumCircuit
from qiskit.result import marginal_counts

from qiskit_experiments.framework import (
    BaseExperiment,
    BaseAnalysis,
    Options,
    ExperimentData,
    AnalysisResultData
)

class CHSHExperiment(BaseExperiment):
    """Custom experiment class template."""

    def __init__(self,
                 physical_qubits: Sequence[int],
                 backend = None):
        """Initialize a chsh bell experiment

        Args:
            physical_qubits: List of physical qubits for the experiment.
            backend: The backend to run the experiment on.

        Raises:
            QiskitError: If any invalid argument is supplied.
        """
        
        
        super().__init__(physical_qubits,
                         analysis = CHSHAnalysis(),
                         backend = backend)

    def circuits(self) -> List[QuantumCircuit]:
        """Generate the list of circuits to be run."""
        
        #Four circuits for this experiment
        #Assume the ideal basis for this inequality
        circuits = []
        for i in range(4):
            qc = QuantumCircuit(2)
            qc.h(0)
            qc.cx(0,1)
            
            #rotate the 2nd qubit by pi/4 (optimal for the inequality)
            qc.rx(np.pi/4,1)
            
            #measure in Z, ZY, YZ, YY 
            if np.mod(i,2):
                qc.sx(0)
            if np.mod(int(i/2),2):
                qc.sx(0)
            qc.measure_all()
            circuits.append(qc)

        return circuits

    @classmethod
    def _default_experiment_options(cls) -> Options:
        """Set default experiment options here."""
        options = super()._default_experiment_options()
        options.update_options(
            shots = 300,
        )
        return options
    

class CHSHAnalysis(BaseAnalysis):
    """Custom analysis class template."""

    @classmethod
    def _default_options(cls) -> Options:
        """Set default analysis options. Plotting is on by default."""

        options = super()._default_options()
        options.dummy_analysis_option = None
        options.plot = False
        options.ax = None
        return options

    def _estate(self, counts):
        #from a counts dictionary determine the correlation function E
        
        shots = np.sum([counts[i] for i in counts])
        return (counts.get('11',0)+counts.get('00',0)-counts.get('10',0)-counts.get('01',0))/shots

    def _run_analysis(
        self,
        experiment_data: ExperimentData,
    ) -> Tuple[List[AnalysisResultData], List["matplotlib.figure.Figure"]]:
        """Run the analysis."""

        # Process the data here
        
        res = experiment_data.data()

        aa = [1,-1,-1,-1]
        S = np.sum([aa[i]*self._estate(res[i]['counts']) for i in range(4)])
        
        analysis_results = [
            AnalysisResultData(name="S", value=S)
        ]
            
        return analysis_results, None


class BellExperiment(BaseExperiment):
    """Custom experiment class template."""

    def __init__(self,
                 layered_coupling_map,
                 cxnum=5,
                 backend = None):
        """Initialize the experiment."""
        
        
        physical_qubits = []
        for layer in layered_coupling_map:
            for pair in layer:
                if pair[0] not in physical_qubits:
                    physical_qubits.append(pair[0])
                if pair[1] not in physical_qubits:
                    physical_qubits.append(pair[1])
        physical_qubits = range(backend.configuration().num_qubits)
        
        self.layered_coupling_map = layered_coupling_map
        self.cxnum = cxnum
        super().__init__(physical_qubits,
                         analysis = BellAnalysis(),
                         backend = backend)

    def circuits(self) -> List[QuantumCircuit]:
        """Generate the list of circuits to be run."""
        conf = self.backend.configuration()
        circuits = make_bell_circs(self.layered_coupling_map, conf, cxnum=self.cxnum)

        return circuits

    @classmethod
    def _default_experiment_options(cls) -> Options:
        """Set default experiment options here."""
        options = super()._default_experiment_options()
        options.update_options(
            shots = 2048,
        )
        return options
    

class BellAnalysis(BaseAnalysis):
    """Custom analysis class template."""

    @classmethod
    def _default_options(cls) -> Options:
        """Set default analysis options. Plotting is on by default."""

        options = super()._default_options()
        options.dummy_analysis_option = None
        options.plot = True
        options.ax = None
        return options

    def _run_analysis(
        self,
        experiment_data: ExperimentData,
    ) -> Tuple[List[AnalysisResultData], List["matplotlib.figure.Figure"]]:
        """Run the analysis."""

        # Process the data here
        from qiskit.quantum_info import hellinger_fidelity
        from qiskit.result import marginal_counts
        import pandas as pd
        
        res = experiment_data.data()

        cxnum = res[0]['metadata']['cxnum']
        if cxnum % 2 == 1: # usual case of making a Bell state
                target = {'00': 0.5, '11': 0.5}
        else: # even number of CX should be an identity
                target = {'00': 0.5, '01': 0.5}
        
        fid = []; cmap=[]
        for datum in res:
            coupling_map = datum['metadata']['coupling_map']
            # cxnum
            counts = datum['counts']
            tmp = extract_ind_counts(coupling_map, counts, measure_idle=False)
            for cr, val in tmp.items():
                cmap.append([int(bit) for bit in cr.split('_')])
                fid.append(hellinger_fidelity(val, target))
        
        df = {'connection':cmap,'fidelity':fid}
        fidelity_data = pd.DataFrame(df).sort_values(by='connection')
        
        
        analysis_results = [
            AnalysisResultData(name="hellinger_fidelities", value=fidelity_data)
        ]
        figures = []
        if self.options.plot:
            figures.append(self._plot(fidelity_data))
            
        return analysis_results, figures

    def _plot(self,data):
        fig, ax = plt.subplots()
        data.sort_values(by='connection').plot(x='connection',y='fidelity',kind='bar',ax=ax)
        return fig


def flatten_bits(crs):
    # it is important to follow bits in int format to match the arrangement
    if len(crs) == 0:
        return []
    else:
        bits=[int(cr[0]) for cr in crs]
        bits.extend([int(cr[1]) for cr in crs])
        return bits
    
def make_bell_circs(layered_coupling_map, conf, cxnum):
    """ 
    run simultaneous bell test. simultaneous pairs are obtained from get_layered_coupling_map
    We assume each cr ran only one time 
    (e.g. [[1_2, 3_4], [5_6, 7_8]] is okay, but [[1_2, 3_4], [1_2, 5_6, 7_8]] is not okay)
    """
    
    from qiskit.transpiler import CouplingMap


    n_reset = 2
    cxnum = 5
    insert_barrier = False

    hadamard_idle = False
    y_basis = False
    measure_idle = False
    circs=[]

    for coupling_map in layered_coupling_map:
        bits=flatten_bits(coupling_map); 
        nbits=len(bits)

        qc = QuantumCircuit(conf.n_qubits, nbits)
        # prepare qubits in superposition and then reset (conditionally) if requested
        if n_reset > 0:
            for bit in bits:
                qc.h(bit)
            for rnum in range(n_reset):
                qc.barrier()
                for bit in bits:
                    qc.reset(bit)
            qc.barrier()
        elif insert_barrier:
            qc.barrier(bits)
        # now do the Bell state
        if hadamard_idle: # Hadamard all qubits except CNOT targets
            for i in range(conf.n_qubits):
                if i not in [edge[1] for edge in coupling_map]:
                    qc.h(i)
        else: #Hadamard only CNOT control qubits
            for edge in coupling_map:
                qc.h(edge[0])
        for i in range(cxnum):
            if insert_barrier:
                qc.barrier(bits)
            for edge in coupling_map:
                    qc.cx(edge[0], edge[1])
                    qc.barrier(edge[0],edge[1])
        if y_basis:
            if insert_barrier:
                qc.barrier(bits)
            for edge in coupling_map:
                qc.s(edge[0])
                qc.sdg(edge[1])
                qc.h(edge[0])
                qc.h(edge[1])
        if measure_idle:
            full_list = list(range(conf.n_qubits))
            qc.measure(full_list, full_list)
        else:
            qc.measure(bits, list(range(nbits)))

        qc.metadata['coupling_map'] = coupling_map
        qc.metadata['cxnum'] = cxnum
        circs.append(qc)
    return circs


def extract_ind_counts(crs, counts, measure_idle):
    # it is important to follow bits in int format to match the arrangement 
    # of classical register in circuit composer in run code
    if not measure_idle:
        bits=flatten_bits(crs); nbits=len(bits)
        bit2idx={}
        for i, bit in enumerate(bits):
            bit2idx.update({int(bit): i})
    # shuffle the data
    ind_counts = {}
    for i, cr in enumerate(crs):
        label='{}_{}'.format(cr[0], cr[1])
        if measure_idle:
            idx1 = int(cr[0])
            idx2 = int(cr[1])
        else:
            idx1 = bit2idx[int(cr[0])]
            idx2 = bit2idx[int(cr[1])]
        ind_counts.update({label:marginal_counts(counts, [idx1, idx2])})
        
        if measure_idle and cr[0] > cr[1]:
            ind_counts[label]['01'], ind_counts[label]['10'] = ind_counts[label].get('10', 0), ind_counts[label].get('01', 0)

    return ind_counts
