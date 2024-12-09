import json
import os
from jsonschema import validate

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_DIR = "schemas"
SCHEMA_MAPPING = {
    "Quantum Volume": "quantum_volume.schema.json",
}


def load_schema(benchmark_name):
    schema_filename = SCHEMA_MAPPING.get(benchmark_name)
    if not schema_filename:
        raise ValueError(f"Unsupported benchmark name: {benchmark_name}")

    with open(os.path.join(CURRENT_DIR, SCHEMA_DIR, schema_filename), "r") as schema_file:
        return json.load(schema_file)


def validate_params(params):
    schema = load_schema(params["benchmark_name"])
    validate(instance=params, schema=schema)


def load_and_validate(file_path):
    with open(os.path.join(CURRENT_DIR, file_path), "r") as file:
        params = json.load(file)
    validate_params(params)
    return params
