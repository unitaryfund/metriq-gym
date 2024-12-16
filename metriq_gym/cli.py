"""Command-line parsing for running metriq benchmarks."""

import argparse
from metriq_gym.job_manager import DEFAULT_FILE_PATH as DEFAULT_JOBS_FILE


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the quantum volume benchmark.

    Returns:
        Parsed arguments as an argparse.Namespace object.
    """
    parser = argparse.ArgumentParser(description="Metriq-Gym benchmarking CLI")
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the file containing the benchmark parameters",
    )
    parser.add_argument(
        "-n", "--num_qubits", type=int, default=8, help="Number of qubits (default is 8)"
    )
    parser.add_argument(
        "-s", "--shots", type=int, default=8, help="Number of shots per trial (default is 8)"
    )
    parser.add_argument(
        "-t", "--trials", type=int, default=8, help="Number of trials (default is 8)"
    )
    parser.add_argument(
        "-a",
        "--action",
        type=str,
        choices=["dispatch", "poll"],
        required=True,
        help="Action to perform: 'dispatch' or 'poll'",
    )
    parser.add_argument(
        "-p",
        "--provider",
        type=str,
        choices=["ibmq", "quantinuum", "ionq"],
        default="ibmq",
        help="String identifier for backend provider service",
    )
    parser.add_argument(
        "-b",
        "--backend",
        type=str,
        default="qasm_simulator",
        help='Backend to use (default is "qasm_simulator")',
    )
    parser.add_argument(
        "-c",
        "--confidence_level",
        type=float,
        default=0.025,
        help="p-value confidence level to use (default is 0.025)",
    )
    parser.add_argument(
        "-j",
        "--jobs_file",
        type=str,
        default=DEFAULT_JOBS_FILE,
        help="File in local directory where async jobs are recorded",
    )
    parser.add_argument(
        "--token", type=str, help="IBM Quantum API token (must be supplied to run on real hardware)"
    )
    parser.add_argument(
        "--instance",
        type=str,
        help="Name of the IBM Quantum plan instance (e.g. 'ibm-q/open/main')",
    )
    return parser.parse_args()
