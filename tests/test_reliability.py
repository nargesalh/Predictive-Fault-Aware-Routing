
import networkx as nx
import pytest

from reliability import all_terminal_reliability_exact


def test_triangle_reliability():
    """A triangle remains connected if at most one edge fails."""
    graph = nx.cycle_graph(3)

    q = 0.1

    expected = (1 - q) ** 3 + 3 * q * (1 - q) ** 2
    actual = all_terminal_reliability_exact(graph, q)

    assert actual == pytest.approx(expected)


def test_path_reliability():
    """A three-node path needs both edges to remain operational."""
    graph = nx.path_graph(3)

    q = 0.1

    expected = (1 - q) ** 2
    actual = all_terminal_reliability_exact(graph, q)

    assert actual == pytest.approx(expected)


def test_reliability_when_failure_probability_is_zero():
    """With no edge failures, a connected graph remains connected."""
    graph = nx.cycle_graph(4)

    assert all_terminal_reliability_exact(graph, 0.0) == pytest.approx(1.0)


def test_reliability_when_failure_probability_is_one():
    """If all edges fail, a graph with multiple vertices is disconnected."""
    graph = nx.path_graph(3)

    assert all_terminal_reliability_exact(graph, 1.0) == pytest.approx(0.0)


def test_disconnected_input_graph_has_zero_reliability():
    """An already disconnected graph cannot become connected by edge failures."""
    graph = nx.Graph()
    graph.add_edges_from([("A", "B"), ("C", "D")])

    assert all_terminal_reliability_exact(graph, 0.1) == pytest.approx(0.0)


@pytest.mark.parametrize("q", [-0.1, 1.1, float("nan"), float("inf")])
def test_invalid_failure_probability(q):
    """Invalid probabilities must be rejected."""
    graph = nx.cycle_graph(3)

    with pytest.raises(ValueError, match="failure_probability"):
        all_terminal_reliability_exact(graph, q)


def test_empty_graph_is_rejected():
    """An empty graph is not a valid reliability input."""
    graph = nx.Graph()

    with pytest.raises(ValueError, match="at least one node"):
        all_terminal_reliability_exact(graph, 0.1)


def test_directed_graph_is_rejected():
    """This implementation supports undirected graphs only."""
    graph = nx.DiGraph()
    graph.add_edge("A", "B")

    with pytest.raises(ValueError, match="undirected"):
        all_terminal_reliability_exact(graph, 0.1)
