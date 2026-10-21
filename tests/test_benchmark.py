
import networkx as nx
import pytest

from experiments.compare_approximations import (
    build_benchmark_graphs,
    run_benchmark,
)


def test_benchmark_graphs_are_connected():
    """Every graph in the benchmark must be connected."""
    graphs = build_benchmark_graphs()

    assert len(graphs) == 5

    for graph in graphs.values():
        assert nx.is_connected(graph)


def test_subway_like_graph_has_degree_two_vertices():
    """The subway-like graph should contain intermediate degree-two nodes."""
    graphs = build_benchmark_graphs()
    graph = graphs["subway_like_small"]

    degree_two_nodes = [
        node
        for node, degree in graph.degree()
        if degree == 2
    ]

    assert len(degree_two_nodes) > 0


def test_benchmark_returns_one_row_per_graph_and_q():
    """Each graph and failure-probability pair should yield one result."""
    graphs = build_benchmark_graphs()
    rows = run_benchmark(q_values=[0.1], repeats=1)

    assert len(rows) == len(graphs)

    for row in rows:
        assert 0.0 <= row["exact_reliability"] <= 1.0
        assert 0.0 <= row["r1_estimate"] <= 1.0
        assert 0.0 <= row["r2_estimate"] <= 1.0


def test_benchmark_errors_match_estimates():
    """Absolute errors must match the stored estimates and exact results."""
    rows = run_benchmark(q_values=[0.1], repeats=1)

    for row in rows:
        assert row["r1_absolute_error"] == pytest.approx(
            abs(
                row["r1_estimate"]
                - row["exact_reliability"]
            )
        )

        assert row["r2_absolute_error"] == pytest.approx(
            abs(
                row["r2_estimate"]
                - row["exact_reliability"]
            )
        )


def test_benchmark_rejects_invalid_repeats():
    """Runtime measurements require a positive number of repetitions."""
    with pytest.raises(ValueError, match="repeats"):
        run_benchmark(q_values=[0.1], repeats=0)


def test_benchmark_rejects_invalid_probability():
    """Failure probabilities must be valid probabilities."""
    with pytest.raises(ValueError, match="Failure probabilities"):
        run_benchmark(q_values=[1.1], repeats=1)
