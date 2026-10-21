
import networkx as nx
import pytest

from reliability import all_terminal_reliability_exact

from reliability import (
    all_terminal_average_reliability_exact,
    all_terminal_reliability_exact,
    estimate_average_reliability,
    sample_edge_deletion_counts,
)


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



def test_exact_average_reliability_triangle():
    """The triangle has average reliability 0.5."""
    graph = nx.cycle_graph(3)

    result = all_terminal_average_reliability_exact(graph)

    assert result == pytest.approx(0.5)


def test_exact_average_reliability_path():
    """A two-edge path has average reliability 1/3."""
    graph = nx.path_graph(3)

    result = all_terminal_average_reliability_exact(graph)

    assert result == pytest.approx(1.0 / 3.0)


def test_edge_deletion_on_cycle():
    """A cycle disconnects after exactly two edge deletions."""
    graph = nx.cycle_graph(4)

    counts = sample_edge_deletion_counts(
        graph,
        trials=100,
        seed=42,
    )

    assert set(counts) == {2}


def test_edge_deletion_estimate_matches_exact_cycle():
    """For a four-edge cycle, the estimator is exactly 2/5."""
    graph = nx.cycle_graph(4)

    estimate = estimate_average_reliability(
        graph,
        trials=100,
        seed=42,
    )

    exact = all_terminal_average_reliability_exact(graph)

    assert estimate == pytest.approx(exact)
    assert estimate == pytest.approx(0.4)


def test_edge_deletion_rejects_disconnected_graph():
    """The deletion process requires a connected input graph."""
    graph = nx.Graph()
    graph.add_nodes_from(["A", "B"])

    
    with pytest.raises(ValueError, match="initially be connected"):
        estimate_average_reliability(graph)



def test_edge_deletion_requires_positive_trials():
    """The number of trials must be positive."""
    graph = nx.cycle_graph(3)

    with pytest.raises(ValueError, match="positive integer"):
        sample_edge_deletion_counts(graph, trials=0)


def test_edge_deletion_is_reproducible():
    """The same seed produces the same deletion sequence results."""
    graph = nx.complete_graph(6)

    first = sample_edge_deletion_counts(
        graph,
        trials=100,
        seed=7,
    )

    second = sample_edge_deletion_counts(
        graph,
        trials=100,
        seed=7,
    )

    assert first == second

