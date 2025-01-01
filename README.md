# metriq-gym

Standard benchmark script implementations for https://metriq.info

## Data

[Benchmark schema is defined here.](https://github.com/unitaryfund/metriq-gym/wiki/Quantum-Volume-definition)

[First hardware results are here.](https://github.com/unitaryfund/metriq-gym/wiki/First-Hardware-Data)

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

```
python metriq_gym/run.py dispatch metriq_gym/schemas/examples/quantum_volume.example.json --backend ibm_strasbourg --provider ibmq
```

Refer to the `schemas/` director for example schema files for other supported benchmarks.


If running on quantum cloud hardware, the job will be added to a polling queue. The status of the queue can be checked with

```
python metriq_gym/run.py poll --job_id <METRIQ_GYM_JOB_ID>
```

where `<METRIQ_GYM_JOB_ID>` is the assigned job ID of the job that was dispatched as provided by `metriq-gym`. 


## Contributing

First, follow the SETUP instructions above.

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
