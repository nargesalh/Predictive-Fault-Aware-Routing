
import networkx as nx
import pytest

from reliability import (
    all_terminal_reliability_exact,
    first_order_approximation,
    second_order_approximation,
)


def test_first_order_approximation_on_triangle():
    """R1 for a triangle follows the degree-based formula."""
    graph = nx.cycle_graph(3)
    q = 0.1

    expected = (1.0 - q**2) ** 3
    actual = first_order_approximation(graph, q)

    assert actual == pytest.approx(expected)


def test_second_order_approximation_on_triangle():
    """R2 for a triangle follows the paper's second-order formula."""
    graph = nx.cycle_graph(3)
    q = 0.1

    expected = (
        (1.0 - q**2) ** 3
        * (1.0 - q**2 * (1.0 - q)) ** 3
    )

    actual = second_order_approximation(graph, q)

    assert actual == pytest.approx(expected)


@pytest.mark.parametrize(
    "approximation",
    [
        first_order_approximation,
        second_order_approximation,
    ],
)
def test_approximations_at_probability_boundaries(approximation):
    """Both approximations handle q=0 and q=1."""
    graph = nx.cycle_graph(4)

    assert approximation(graph, 0.0) == pytest.approx(1.0)
    assert approximation(graph, 1.0) == pytest.approx(0.0)


@pytest.mark.parametrize(
    "approximation",
    [
        first_order_approximation,
        second_order_approximation,
    ],
)
@pytest.mark.parametrize("q", [0.01, 0.1, 0.3, 0.7, 0.99])
def test_approximation_output_is_a_probability(approximation, q):
    """Approximation results must remain between zero and one."""
    graph = nx.cycle_graph(5)

    result = approximation(graph, q)

    assert 0.0 <= result <= 1.0


@pytest.mark.parametrize(
    "approximation",
    [
        first_order_approximation,
        second_order_approximation,
    ],
)
def test_invalid_probability_is_rejected(approximation):
    """Invalid failure probabilities must raise ValueError."""
    graph = nx.cycle_graph(3)

    for q in [-0.1, 1.1, float("nan"), float("inf"), True]:
        with pytest.raises(ValueError, match="failure_probability"):
            approximation(graph, q)


@pytest.mark.parametrize(
    "approximation",
    [
        first_order_approximation,
        second_order_approximation,
    ],
)
def test_disconnected_graph_is_rejected(approximation):
    """The approximation formulas require a connected input graph."""
    graph = nx.Graph()
    graph.add_edges_from([("A", "B"), ("C", "D")])

    with pytest.raises(ValueError, match="graph must be connected"):
        approximation(graph, 0.1)


@pytest.mark.parametrize(
    "approximation",
    [
        first_order_approximation,
        second_order_approximation,
    ],
)
def test_directed_graph_is_rejected(approximation):
    """The implemented formulas support undirected graphs only."""
    graph = nx.DiGraph()
    graph.add_edge("A", "B")

    with pytest.raises(ValueError, match="undirected"):
        approximation(graph, 0.1)


def test_exact_reliability_on_triangle():
    """The exact reliability of a triangle is known analytically."""
    graph = nx.cycle_graph(3)
    q = 0.1

    exact = all_terminal_reliability_exact(graph, q)

    assert exact == pytest.approx(0.972)


def test_approximations_can_be_compared_with_exact_result():
    """The approximations and exact method solve the same reliability task."""
    graph = nx.cycle_graph(3)
    q = 0.1

    exact = all_terminal_reliability_exact(graph, q)
    first_order = first_order_approximation(graph, q)
    second_order = second_order_approximation(graph, q)

    assert exact == pytest.approx(0.972)
    assert first_order == pytest.approx((1.0 - q**2) ** 3)
    assert second_order == pytest.approx(
        (1.0 - q**2) ** 3
        * (1.0 - q**2 * (1.0 - q)) ** 3
    )

    # Do not assume R2 is always more accurate than R1.
    assert all(0.0 <= value <= 1.0 for value in [
        exact,
        first_order,
        second_order,
    ])
