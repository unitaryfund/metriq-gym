# metriq-gym

Standard benchmark script implementations for https://metriq.info

## Data

[Benchmark schema is defined here.](https://github.com/unitaryfund/metriq-gym/wiki/Quantum-Volume-definition)

[First hardware results are here.](https://github.com/unitaryfund/metriq-gym/wiki/First-Hardware-Data)

## Setup

You will require **Python 3.12** and [`poetry`](https://python-poetry.org/). **Note:** the
newest Python version 3.13 is not yet supported due to the `qiskit-aer` dependency.

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

To run on hardware, you will also require an IBM token. To obtain this, please
visit the [IBM Quantum Platform](https://quantum.ibm.com/).

Otherwise, if you are running on a simulator, once you have invoked the `poetry
shell` command as described above, run:

```
python metriq_gym/dispatch_qv.py
```
for Quantum Volume benchmarks or
```
python metriq_gym/dispatch_clops.py
```
for CLOPS.

Doing so will yield output similar to the following (if running on a simulator):

```
2024-10-08 14:38:43,117 - INFO - Aggregated results over 8 trials: {'qubits': 16, 'seconds': 0.7648332118988037, 'sim_seconds': 1.2858296614140272, 'hog_prob': 0.4239501953125, 'pass': False, 'p-value': np.float64(0.0), 'clops': 10967891.913550833, 'sim_clops': 6523887.457048584}
{'qubits': 16, 'seconds': 0.7648332118988037, 'sim_seconds': 1.2858296614140272, 'hog_prob': 0.4239501953125, 'pass': False, 'p-value': np.float64(0.0), 'clops': 10967891.913550833, 'sim_clops': 6523887.457048584}
```

If running on quantum cloud hardware, the job will be added to a polling queue. The status of the queue can be checked with
```
python metriq_gym/poll_qv.py
```
or
```
python metriq_gym/poll_clops.py
```
at which point, any completed jobs results will be printed.


If you wish to specify more command line arguments and run on hardware (assuming
that you have obtained your IBM token) you can run:

```
python metriq_gym/poll_qv.py -n 2 --shots 1024 --backend ibm_sherbrooke --token <IBM_TOKEN>
```

where `<IBM_TOKEN>` is the token obtain from the IBM jobs platform.

## Contributing

### Cloning the repo
When cloning the metriq-gym repository use:

```sh
git clone --recurse-submodules https://github.com/unitaryfund/metriq-gym.git
```

We have [qiskit-device-benchmarking](https://github.com/qiskit-community/qiskit-device-benchmarking) as a git submodule
for a set of some of the IBM benchmarks. If you’ve already cloned the repository without the submodules, you can
initialize them with:

```sh
git submodule update --init --recursive
```

Updating the submodule: To pull the latest changes from the submodule’s repository:

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
