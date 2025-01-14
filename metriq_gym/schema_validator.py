import json
import os
from typing import Any
from jsonschema import validate
from pydantic import BaseModel, create_model

from metriq_gym.benchmarks import SCHEMA_MAPPING
from metriq_gym.job_type import JobType


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEMA_DIR = os.path.join(CURRENT_DIR, "schemas")


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
    schema_filename = SCHEMA_MAPPING.get(JobType(benchmark_name))
    if not schema_filename:
        raise ValueError(f"Unsupported benchmark: {benchmark_name}")

    schema_path = os.path.join(schema_dir, schema_filename)
    return load_json_file(schema_path)


def validate_params(params: dict, schema: dict[str, Any]) -> None:
    """
    Validate parameters against the corresponding JSON schema.
    Raises a ValidationError if the parameters do not match the schema.
    """
    validate(instance=params, schema=schema)


def create_pydantic_model(schema: dict[str, Any]) -> Any:
    type_mapping = {
        "string": (str, ...),
        "integer": (int, ...),
        "number": (float, ...),
        "boolean": (bool, ...),
        "array": (list, ...),
        "object": (dict, ...),
    }
    fields = {k: type_mapping[v["type"]] for k, v in schema["properties"].items()}
    model = create_model(schema["title"], **fields)
    model.model_rebuild()
    return model


def load_and_validate(file_path: str, schema_dir: str = DEFAULT_SCHEMA_DIR) -> BaseModel:
    """
    Load parameters from a JSON file and validate them against the corresponding schema.
    Raises a ValidationError validation fails.
    """
    params = load_json_file(file_path)
    schema = load_schema(params.get("benchmark_name"), schema_dir)
    validate_params(params, schema)

    model = create_pydantic_model(schema)
    return model(**params)
