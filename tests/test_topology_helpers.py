import rustworkx as rx
from metriq_gym.topology_helpers import largest_connected_size


def test_largest_connected_size_single_component():
    # Create a C5 graph with a single connected component
    graph = rx.PyGraph()
    graph.add_nodes_from(range(5))
    graph.add_edges_from([(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 4, 1)])

    assert largest_connected_size(graph) == 5


def test_largest_connected_size_multiple_components():
    # Create a graph with two connected components
    graph = rx.PyGraph()
    graph.add_nodes_from(range(7))
    graph.add_edges_from([(0, 1, 1), (1, 2, 1), (3, 4, 1), (4, 5, 1)])
    print(graph)
    assert largest_connected_size(graph) == 3


def test_largest_connected_size_disconnected_nodes():
    # Create a graph with disconnected nodes
    graph = rx.PyGraph()
    graph.add_nodes_from(range(5))
    graph.add_edges_from([(0, 1, 1), (2, 3, 1)])

    assert largest_connected_size(graph) == 2


def test_largest_connected_size_empty_graph():
    # Create an empty graph
    graph = rx.PyGraph()

    assert largest_connected_size(graph) == 0
