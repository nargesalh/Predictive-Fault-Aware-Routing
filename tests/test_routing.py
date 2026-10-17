
import pytest

from main import (
    build_network,
    find_shortest_route,
    get_operational_graph,
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
