
import networkx as nx
import pytest

from reliability import (
    SubwayApproximationNotApplicable,
    all_terminal_reliability_exact,
    subway_type_approximation,
)


def build_small_subway_graph():
    """Create three internally disjoint paths between two junctions."""
    graph = nx.Graph()

    paths = [
        ["A", "x1", "B"],
        ["A", "y1", "y2", "B"],
        ["A", "z1", "z2", "z3", "B"],
    ]

    for path in paths:
        graph.add_edges_from(zip(path, path[1:]))

    return graph


def test_subway_formula_on_degree_two_paths():
    """Rs should equal the product of the paper's path factors."""
    graph = build_small_subway_graph()
    q = 0.1
    p = 1.0 - q

    expected = (
        (p**2 + 2 * q * p)
        * (p**3 + 3 * q * p**2)
        * (p**4 + 4 * q * p**3)
    )

    actual = subway_type_approximation(graph, q)

    assert actual == pytest.approx(expected)


def test_subway_approximation_matches_exact_cycle_reliability():
    """The cycle special case is exact."""
    graph = nx.cycle_graph(5)
    q = 0.2

    approximate = subway_type_approximation(graph, q)
    exact = all_terminal_reliability_exact(graph, q)

    assert approximate == pytest.approx(exact)


def test_subway_approximation_matches_exact_tree_reliability():
    """Every edge of a tree must work for all vertices to stay connected."""
    graph = nx.path_graph(5)
    q = 0.2

    approximate = subway_type_approximation(graph, q)
    exact = all_terminal_reliability_exact(graph, q)

    assert approximate == pytest.approx(exact)


def test_removed_leaf_edges_contribute_reliability_factor():
    """Adding a leaf multiplies reliability by its edge-up probability."""
    graph = build_small_subway_graph()
    q = 0.1

    base_result = subway_type_approximation(graph, q)

    graph_with_leaf = graph.copy()
    graph_with_leaf.add_edge("A", "leaf")

    result_with_leaf = subway_type_approximation(graph_with_leaf, q)

    assert result_with_leaf == pytest.approx(
        (1.0 - q) * base_result
    )


def test_direct_junction_edge_is_not_supported():
    """Rs should reject a direct edge between two junctions."""
    graph = nx.Graph()

    graph.add_edges_from(
        [
            ("A", "B"),
            ("A", "x1"),
            ("x1", "B"),
            ("A", "y1"),
            ("y1", "B"),
        ]
    )

    with pytest.raises(SubwayApproximationNotApplicable):
        subway_type_approximation(graph, 0.1)


@pytest.mark.parametrize("q", [0.0, 1.0])
def test_subway_approximation_probability_boundaries(q):
    """Reliability is one at q=0 and zero at q=1."""
    graph = build_small_subway_graph()

    expected = 1.0 if q == 0.0 else 0.0

    assert subway_type_approximation(graph, q) == pytest.approx(expected)


@pytest.mark.parametrize(
    "q",
    [-0.1, 1.1, float("nan"), float("inf"), True],
)
def test_invalid_failure_probability_is_rejected(q):
    """Invalid failure probabilities must raise ValueError."""
    graph = build_small_subway_graph()

    with pytest.raises(ValueError, match="failure_probability"):
        subway_type_approximation(graph, q)


def test_disconnected_graph_is_rejected():
    """The input graph must be connected."""
    graph = nx.Graph()
    graph.add_edges_from([("A", "B"), ("C", "D")])

    with pytest.raises(ValueError, match="graph must be connected"):
        subway_type_approximation(graph, 0.1)


def test_original_graph_is_not_modified():
    """The algorithm must preserve the input graph."""
    graph = build_small_subway_graph()
    original_edges = set(graph.edges())

    subway_type_approximation(graph, 0.1)

    assert set(graph.edges()) == original_edges

def test_subway_approximation_rejects_bridge_in_core():
    """Rs must reject a core containing a bridge."""
    graph = nx.barbell_graph(3, 1)

    with pytest.raises(
        SubwayApproximationNotApplicable,
        match="bridge-free core",
    ):
        subway_type_approximation(graph, 0.1)