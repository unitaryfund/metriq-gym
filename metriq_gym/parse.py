"""Command-line parsing for running metriq benchmarks."""
import argparse

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the quantum volume benchmark.

    Returns:
        Parsed arguments as an argparse.Namespace object.
    """
    parser = argparse.ArgumentParser(description="Quantum volume certification")
    parser.add_argument("-n", type=int, default=8, help="Number of qubits")
    parser.add_argument("-s", "--shots", type=int, default=None, help="Number of shots (default is 2^n)")
    parser.add_argument("-t", "--trials", type=int, default=8, help="Number of trials to run")
    parser.add_argument("-b", "--backend", type=str, default="qasm_simulator", help="Backend to use")
    parser.add_argument("--token", type=str, help="IBM Quantum API token")

    args = parser.parse_args()

    if args.shots is None:
        args.shots = 1 << args.n  # Default to 2^n shots

    return args
