# metriq-gym

Standard benchmark script implementations for https://metriq.info

## Setup

You will require Python 3.12 and [`poetry`](https://python-poetry.org/).

Once you have `poetry` installed, run:

```sh
poetry install
poetry shell
```

To run on hardware, you will also require an IBM token. To obtain this, please
visit the [IBM Quantum Platform](https://quantum.ibm.com/).

Otherwise, if you are running on a simulator, once you have invoked the `poetry
shell` command as described above, run:

```
python metriq_gym/hardware/qv_clops_qiskit.py
```

Doing so will yield output similar to the following:

```
2024-10-08 14:38:43,117 - INFO - Aggregated results over 8 trials: {'qubits': 16, 'seconds': 0.7648332118988037, 'sim_seconds': 1.2858296614140272, 'hog_prob': 0.4239501953125, 'pass': False, 'p-value': np.float64(0.0), 'clops': 10967891.913550833, 'sim_clops': 6523887.457048584}
{'qubits': 16, 'seconds': 0.7648332118988037, 'sim_seconds': 1.2858296614140272, 'hog_prob': 0.4239501953125, 'pass': False, 'p-value': np.float64(0.0), 'clops': 10967891.913550833, 'sim_clops': 6523887.457048584}
```
