from pytket.extensions.quantinuum import QuantinuumBackend
from pytket.extensions.qiskit import qiskit_to_tk

import random
import time

from pyqrack import QrackSimulator
from qiskit_aer import Aer
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit import QuantumCircuit
from qiskit.compiler import transpile

from pytket.extensions.quantinuum.backends.api_wrappers import QuantinuumAPI
from pytket.extensions.quantinuum.backends.credential_storage import (
    QuantinuumConfigCredentialStorage,
)

from metriq_gym.bench import random_circuit_sampling

n = 5
trials = 10

device = QuantinuumBackend('H1-1E')
sim_device = Aer.get_backend("qasm_simulator")

circs = []
ideal_probs = []
sim_interval = 0

for _ in range(trials):
    circ = random_circuit_sampling(n)
    sim_circ = circ.copy()
    circ.measure_all()

    circs.append(circ)
    circ = transpile(circ, sim_device) # I changed this for now.

    start = time.perf_counter()
    sim = QrackSimulator(n)
    sim.run_qiskit_circuit(sim_circ, shots=0)
    ideal_probs.append(sim.out_probs())
    del sim
    sim_interval += time.perf_counter() - start


tket_circs = [qiskit_to_tk(circ) for circ in circs]
#job = device.run(circs, shots=shots)

backend = QuantinuumBackend(
    device_name="H1-1E",
    api_handler=QuantinuumAPI(token_store=QuantinuumConfigCredentialStorage()),
)

compiled_circ = backend.get_compiled_circuit(tket_circs[0])
handle = backend.process_circuit(compiled_circ, n_shots=1000)
print(handle)

# Retrieve partial shots:counts from the handle of an unfinished job
partial_result, job_status = backend.get_partial_result(handle)
print(partial_result)
print(job_status)
print(partial_result.get_counts())


