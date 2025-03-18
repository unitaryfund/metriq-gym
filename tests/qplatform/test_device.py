from unittest.mock import MagicMock
import pytest
from qbraid import QuantumDevice
from qbraid.runtime import QiskitBackend

from rustworkx import PyGraph

from metriq_gym.qplatform.device import connectivity_graph


def test_device_connectivity_graph_qiskit_backend():
    mock_backend = MagicMock()
    mock_graph = PyGraph()
    mock_graph.add_nodes_from(range(3))
    mock_graph.add_edge(0, 1, None)
    mock_graph.add_edge(1, 2, None)
    mock_backend.coupling_map.graph.to_undirected.return_value = mock_graph

    mock_device = MagicMock(spec=QiskitBackend)
    mock_device._backend = mock_backend

    graph = connectivity_graph(mock_device)

    assert isinstance(graph, PyGraph)
    assert set(graph.nodes()) == {0, 1, 2}
    assert set(graph.edge_list()) == {(0, 1), (1, 2)}


def test_device_connectivity_graph_invalid_device():
    mock_device = MagicMock(spec=QuantumDevice)  # Mock an unknown QuantumDevice
    with pytest.raises(NotImplementedError, match="Connectivity graph not implemented for device"):
        connectivity_graph(mock_device)
