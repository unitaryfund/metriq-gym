import json
import pytest
from jsonschema import ValidationError
from metriq_gym.schema_validator import load_and_validate, validate_params, SCHEMA_MAPPING


@pytest.fixture
def mock_schema(tmpdir):
    schema_content = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "benchmark_name": {"type": "string", "const": "Test Benchmark"},
            "num_qubits": {"type": "integer", "minimum": 1},
            "shots": {"type": "integer", "minimum": 1},
            "trials": {"type": "integer", "minimum": 1},
        },
        "required": ["benchmark_name", "num_qubits"],
    }
    schema_file_path = tmpdir.join("test.schema.json")
    with open(schema_file_path, "w") as schema_file:
        json.dump(schema_content, schema_file)

    SCHEMA_MAPPING["Test Benchmark"] = str(schema_file_path)
    return SCHEMA_MAPPING


@pytest.fixture
def valid_params():
    return {
        "benchmark_name": "Test Benchmark",
        "num_qubits": 5,
        "shots": 1024,
        "trials": 10,
    }


@pytest.fixture
def invalid_params():
    return {
        "benchmark_name": "Test Benchmark",
        "num_qubits": 0,  # Invalid value
        "shots": 1024,
        "trials": 10,
    }


@pytest.fixture
def file_path_valid_job(valid_params, tmpdir):
    file_path = tmpdir.join("valid_job.json")
    with open(file_path, "w") as file:
        json.dump(valid_params, file)
    return str(file_path)


@pytest.fixture
def file_path_invalid_job(invalid_params, tmpdir):
    file_path = tmpdir.join("invalid_job.json")
    with open(file_path, "w") as file:
        json.dump(invalid_params, file)
    return str(file_path)


def test_load_and_validate_valid(file_path_valid_job, valid_params, mock_schema):
    params = load_and_validate(file_path_valid_job)
    assert params == valid_params


def test_load_and_validate_invalid(file_path_invalid_job, mock_schema):
    with pytest.raises(ValidationError):
        load_and_validate(file_path_invalid_job)


def test_validate_params_valid(valid_params, mock_schema):
    validate_params(valid_params)


def test_validate_params_invalid(invalid_params, mock_schema):
    with pytest.raises(ValidationError):
        validate_params(invalid_params)


def test_load_and_validate_invalid_job_path():
    with pytest.raises(FileNotFoundError):
        load_and_validate("invalid_job.json")
