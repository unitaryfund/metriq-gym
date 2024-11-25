"""Gate-based utility functions."""

import math
import random
from qiskit import QuantumCircuit, qasm3
from pytket.circuit import Circuit
from pytket.extensions.qiskit import qiskit_to_tk as _qiskit_to_tk
from pyqrack import QrackCircuit


def qiskit_to_qasm(circ: QuantumCircuit) -> str:
    """Convert a Qiskit QuantumCircuit to an OpenQASM 3 string

    Args:
        circ: QuantumCircuit to translate to OpenQASM 3
    """
    return qasm3.dumps(circ)


def qasm_to_qiskit(qasm: str) -> QuantumCircuit:
    """Convert an OpenQASM 3 string to a Qiskit QuantumCircuit

    Args:
        circ: OpenQASM 3 string to translate to QuantumCircuit
    """
    return QuantumCircuit.from_qasm_str(str)


def qiskit_to_tk(circ: QuantumCircuit) -> Circuit:
    """Convert a Qiskit QuantumCircuit to a pytket circuit

    Args:
        circ: QuantumCircuit to translate to pytket
    """
    return _qiskit_to_tk(circ)


def qiskit_to_qrack(circ: QuantumCircuit) -> QrackCircuit:
    """Convert a Qiskit QuantumCircuit to a QrackCircuit

    Args:
        circ: QuantumCircuit to translate to QrackCircuit
    """
    return QrackCircuit.in_from_qiskit_circuit(circ)


def qrack_to_qiskit(circ: QrackCircuit) -> QuantumCircuit:
    """Convert a QrackCircuit to a Qiskit QuantumCircuit

    Args:
        circ: QrackCircuit to translate to QuantumCircuit
    """
    return circ.to_qiskit_circuit()


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


def qiskit_random_circuit_sampling(n: int) -> QuantumCircuit:
    """Generate a square circuit, for random circuit sampling

    Args:
        n: Width of circuit to generate.
    """
    circ = QuantumCircuit(n)
    for _ in range(n):
        for i in range(n):
            rand_u3(circ, i)

        unused_bits = list(range(n))
        random.shuffle(unused_bits)
        while len(unused_bits) > 1:
            c = unused_bits.pop()
            t = unused_bits.pop()
            circ.cx(c, t)
    return circ
