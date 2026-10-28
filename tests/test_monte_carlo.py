
import networkx as nx
import pytest

from reliability import (
    estimate_all_terminal_reliability_monte_carlo,
)


@pytest.mark.parametrize(
    ("failure_probability", "expected"),
    [(0.0, 1.0), (1.0, 0.0)],
)
def test_extreme_failure_probabilities(
    failure_probability,
    expected,
):
    graph = nx.path_graph(4)

    result = estimate_all_terminal_reliability_monte_carlo(
        graph,
        failure_probability,
        trials=100,
        seed=42,
    )

    assert result == expected


def test_seed_makes_results_reproducible():
    graph = nx.complete_graph(5)

    first = estimate_all_terminal_reliability_monte_carlo(
        graph, 0.2, trials=1000, seed=42
    )
    second = estimate_all_terminal_reliability_monte_carlo(
        graph, 0.2, trials=1000, seed=42
    )

    assert first == second


@pytest.mark.parametrize(
    "failure_probability",
    [-0.1, 1.1, float("nan"), True],
)
def test_invalid_failure_probability_is_rejected(
    failure_probability,
):
    with pytest.raises(ValueError):
        estimate_all_terminal_reliability_monte_carlo(
            nx.path_graph(3),
            failure_probability,
        )


@pytest.mark.parametrize("trials", [0, -1, 1.5, True])
def test_invalid_trial_count_is_rejected(trials):
    with pytest.raises(ValueError):
        estimate_all_terminal_reliability_monte_carlo(
            nx.path_graph(3),
            0.2,
            trials=trials,
        )


def test_empty_graph_is_rejected():
    with pytest.raises(ValueError, match="at least one node"):
        estimate_all_terminal_reliability_monte_carlo(
            nx.Graph(),
            0.2,
        )
