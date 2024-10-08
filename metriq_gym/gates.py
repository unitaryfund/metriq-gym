import math
import random
from qiskit import QuantumCircuit


def rand_u3(circ: QuantumCircuit, q: int) -> None:
    """Apply a random U3 gate to a specified qubit in the given quantum circuit.

    Args:
        circ: QuantumCircuit instance representing the circuit.
        q: The qubit index in the circuit where the U3 gate will be applied.
    """
    th = random.uniform(0, 2 * math.pi)
    ph = random.uniform(0, 2 * math.pi)
    lm = random.uniform(0, 2 * math.pi)
    circ.u(th, ph, lm, q)


def coupler(circ: QuantumCircuit, q1: int, q2: int) -> None:
    """Apply a CNOT (CX) gate between two qubits in the given quantum circuit.

    Args:
        circ: QuantumCircuit instance representing the circuit.
        q1: The control qubit index for the CNOT gate.
        q2: The target qubit index for the CNOT gate.
    """
    circ.cx(q1, q2)
