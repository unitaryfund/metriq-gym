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
python metriq_gym/hardware/qv_clops_qiskit.py -n 2 --shots 1024 --backend ibm_sherbrooke --token <IBM_TOKEN>
```

where `<IBM_TOKEN>` is the token obtain from the IBM jobs platform.
