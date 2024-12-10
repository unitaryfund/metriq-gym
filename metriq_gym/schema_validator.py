import json
import os
from jsonschema import validate


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEMA_DIR = os.path.join(CURRENT_DIR, "schemas")

SCHEMA_MAPPING = {
    "Quantum Volume": "quantum_volume.schema.json",
}


def load_json_file(file_path: str) -> dict:
    """
    Load and parse a JSON file.
    """
    with open(file_path, "r") as file:
        return json.load(file)


def load_schema(benchmark_name: str, schema_dir: str = DEFAULT_SCHEMA_DIR) -> dict:
    """
    Load a JSON schema based on the benchmark name.
    """
    schema_filename = SCHEMA_MAPPING.get(benchmark_name)
    if not schema_filename:
        raise ValueError(f"Unsupported benchmark: {benchmark_name}")

    schema_path = os.path.join(schema_dir, schema_filename)
    return load_json_file(schema_path)


def validate_params(params: dict, schema_dir: str = DEFAULT_SCHEMA_DIR) -> None:
    """
    Validate parameters against the corresponding JSON schema.
    Raises a ValidationError if the parameters do not match the schema.
    """
    schema = load_schema(params.get("benchmark_name"), schema_dir)
    validate(instance=params, schema=schema)


def load_and_validate(file_path: str, schema_dir: str = DEFAULT_SCHEMA_DIR) -> dict:
    """
    Load parameters from a JSON file and validate them against the corresponding schema.
    Raises a ValidationError validation fails.
    """
    params = load_json_file(file_path)
    validate_params(params, schema_dir)
    return params
