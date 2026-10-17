
import random

import networkx as nx
import pytest

from main import (
    build_network,
    estimate_two_terminal_reliability,
    find_shortest_route,
    get_operational_graph,
    sample_network_state,
)


def test_initial_route():
    """The initial network should use the lowest-latency route."""
    graph = build_network()

    path, latency = find_shortest_route(graph, "A", "F")

    assert path == ["A", "C", "D", "E", "F"]
    assert latency == pytest.approx(4.6)


def test_route_changes_after_link_failure():
    """The route should avoid the failed C-D link."""
    graph = build_network()
    graph.edges["C", "D"]["is_up"] = False

    path, latency = find_shortest_route(graph, "A", "F")

    assert path == ["A", "C", "B", "D", "E", "F"]
    assert latency == pytest.approx(4.8)
    assert ("C", "D") not in list(zip(path, path[1:]))


def test_no_route_when_all_links_fail():
    """The function should report when no route is available."""
    graph = build_network()

    for u, v in graph.edges:
        graph.edges[u, v]["is_up"] = False

    path, latency = find_shortest_route(graph, "A", "F")

    assert path is None
    assert latency is None


def test_operational_graph_does_not_modify_original():
    """Removing failed links must not change the original graph."""
    graph = build_network()
    graph.edges["C", "D"]["is_up"] = False

    operational = get_operational_graph(graph)

    assert graph.has_edge("C", "D")
    assert not operational.has_edge("C", "D")


def test_monte_carlo_estimates_known_path_reliability():
    """A two-link path with p=0.9 has reliability 0.81."""
    graph = nx.Graph()
    graph.add_edge("A", "B", probability_up=0.9, is_up=True)
    graph.add_edge("B", "C", probability_up=0.9, is_up=True)

    estimate = estimate_two_terminal_reliability(
        graph,
        "A",
        "C",
        trials=20_000,
        seed=42,
    )

    assert estimate == pytest.approx(0.81, abs=0.02)


def test_monte_carlo_is_reproducible():
    """The same seed and inputs should give the same estimate."""
    graph = build_network()

    first = estimate_two_terminal_reliability(
        graph, "A", "F", trials=1_000, seed=7
    )

    second = estimate_two_terminal_reliability(
        graph, "A", "F", trials=1_000, seed=7
    )

    assert first == second


def test_trials_must_be_positive():
    """A simulation must contain at least one trial."""
    graph = build_network()

    with pytest.raises(ValueError, match="positive integer"):
        estimate_two_terminal_reliability(
            graph, "A", "F", trials=0
        )


def test_sampling_does_not_modify_original_graph():
    """Sampling should leave the original link states unchanged."""
    graph = build_network()

    sample_network_state(graph, random.Random(123))

    assert all(
        data["is_up"]
        for _, _, data in graph.edges(data=True)
    )
