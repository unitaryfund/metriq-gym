# `metriq-gym`

[![Unitary Foundation](https://img.shields.io/badge/Supported%20By-Unitary%20Foundation-FFFF00.svg)](https://unitary.foundation)
[![Discord Chat](https://img.shields.io/badge/dynamic/json?color=blue&label=Discord&query=approximate_presence_count&suffix=%20online.&url=https%3A%2F%2Fdiscord.com%2Fapi%2Finvites%2FJqVGmpkP96%3Fwith_counts%3Dtrue)](http://discord.unitary.foundation)


`metriq-gym` is a Python framework for implementing and running standard quantum benchmarks on different quantum devices by different providers.

- _Open_ – Open-source since its inception and fully developed in public.
- _Transparent_ – All benchmark parameters are defined in a schema file and the benchmark code is reviewable by the community.
- _Cross-platform_ – Supports running benchmarks on multiple quantum hardware providers (_integration powered by [qBraid-SDK](https://github.com/qBraid/qBraid)_)
- _User-friendly_ – Provides a simple command-line interface for dispatching, monitoring, and polling benchmark jobs (you can go on with your life while your job waits in the queue).

Data generated by metriq-gym is intended to be published on https://metriq.info.

**Join the conversation!** 
- For code, repo, or theory questions, especially those requiring more detailed responses, submit a [Discussion](https://github.com/unitaryfund/metriq-gym/discussions).
- For casual or time sensitive questions, chat with us on [Discord](http://discord.unitary.foundation)'s `#metriq` channel.


## Setup

You will require **Python 3.12** and [`poetry`](https://python-poetry.org/). **Note:** the
newest Python version 3.13 is not yet supported due to the `qiskit-aer` dependency.

### Cloning the repo
When cloning the metriq-gym repository use:

```sh
git clone --recurse-submodules https://github.com/unitaryfund/metriq-gym.git
```

This allows you to fetch [qiskit-device-benchmarking](https://github.com/qiskit-community/qiskit-device-benchmarking) as a git submodule
for a set of some of the IBM benchmarks.

### Installation
Once you have `poetry` installed, run:

```sh
poetry install
poetry shell
```

## Running on hardware

### Credential management

To run on hardware, each hardware provider offers API tokens that are required to interact with their quantum devices.
In order to run on these devices, you will need to follow the instructions on the respective pages of the providers and
obtain API keys from them.

The `.env.example` file illustrates how to specify the API keys once you have acquired them. You will need to create a
`.env` file in the same directory as `.env.example` and populate the values of these variables accordingly.

### Example

To run on IBM hardware, you will also require an IBM token. To obtain this, please
visit the [IBM Quantum Platform](https://quantum.ibm.com/).

Once you have invoked the `poetry shell` command as described above, you can dispatch a job by specifying the parameters of the job you wish to launch in a configuration file. The following dispatches a job on the ibm-strasbourg device for quantum volume.

```sh
python metriq_gym/run.py dispatch metriq_gym/schemas/examples/quantum_volume.example.json --provider ibm --device ibm_strasbourg 
```

Refer to the `schemas/` director for example schema files for other supported benchmarks.


If running on quantum cloud hardware, the job will be added to a polling queue. The status of the queue can be checked with

```sh
python metriq_gym/run.py poll --job_id <METRIQ_GYM_JOB_ID>
```

where `<METRIQ_GYM_JOB_ID>` is the assigned job ID of the job that was dispatched as provided by `metriq-gym`. 

Alternatively, the `poll` action can be used without the `--job_id` flag to view all dispatched jobs, 
and select the one that is of interest.

```sh
python metriq_gym/run.py poll
```

### Listing jobs

You can view all the jobs that have been dispatched by using the `list-jobs` action. This will read the `jobs_file`
and display information about each job, including its ID, backend, job type, provider, qubits, and shots.

```sh
python metriq_gym/run.py list-jobs
```

## Contributing

First, follow the [Setup](#setup) instructions above.

### Updating the submodule
To pull the latest changes from the submodule’s repository:

```sh
cd submodules/qiskit-device-benchmarking
git pull origin main
```

Then, commit the updated submodule reference in your main repository.

### Style guide
We don't have a style guide per se, but we recommend that both linter and formatter 
are run before each commit. In order to guarantee that, please install the pre-commit hook with

```sh
poetry run pre-commit install
```
immediately upon cloning the repository.

### Tests
The suite of unit tests can be run with
```sh
poetry run pytest
```

### Type checking
The project uses [mypy](https://mypy.readthedocs.io/en/stable/) for static type checking. To run mypy, use the following command:
```sh
poetry run mypy
```

### Documentation
The project uses [Sphinx](https://www.sphinx-doc.org/en/master/) to generate documentation. To build the HTML
documentation:

1.Navigate to the docs/ directory:
```sh
cd docs/
```

Run the following command to build the HTML files:
```sh
make html
```

Open the generated `index.html` file located in the `_build/html/` directory to view the documentation.

## Data

[Benchmark schema is defined here.](https://github.com/unitaryfund/metriq-gym/wiki/Quantum-Volume-definition)

[First hardware results are here.](https://github.com/unitaryfund/metriq-gym/wiki/First-Hardware-Data)

