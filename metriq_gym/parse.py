"""Command-line parsing for running metriq benchmarks."""
import argparse

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the quantum volume benchmark.

    Returns:
        Parsed arguments as an argparse.Namespace object.
    """
    parser = argparse.ArgumentParser(description="Quantum volume certification")
    parser.add_argument("-n", "--num_qubits", type=int, default=8, help="Number of qubits (default is 8)")
    parser.add_argument("-s", "--shots", type=int, default=8, help="Number of shots per trial (default is 8)")
    parser.add_argument("-t", "--trials", type=int, default=8, help="Number of trials (default is 8)")
    parser.add_argument("-b", "--backend", type=str, default="qasm_simulator", help="Backend to use (default is \"qasm_simulator\")")
    parser.add_argument("-c", "--confidence_level", type=float, default=0.025, help="p-value confidence level to use (default is 0.025)")
    parser.add_argument("-j", "--jobs_file", type=str, default=".metriq_gym_jobs.json", help="File in local directory where async jobs are recorded")
    parser.add_argument("--token", type=str, help="IBM Quantum API token (must be supplied to run on real hardware)")
    parser.add_argument("--instance", type=str, help="Name of the IBM Quantum plan instance (e.g. 'ibm-q/open/main')")

    args = parser.parse_args()

    return args
