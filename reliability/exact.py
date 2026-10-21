
from math import comb
from numbers import Real

import networkx as nx


def _validate_graph(graph):
    """Validate the graph type used by reliability algorithms."""
    if not isinstance(graph, nx.Graph):
        raise TypeError("graph must be a NetworkX graph.")

    if graph.is_directed():
        raise ValueError("Only undirected graphs are supported.")

    if graph.is_multigraph():
        raise ValueError("Parallel edges are not supported.")

    if graph.number_of_nodes() == 0:
        raise ValueError("graph must contain at least one node.")


def all_terminal_reliability_exact(graph, failure_probability):
    """
    Compute exact all-terminal reliability for an undirected graph.

    Edges fail independently with the same probability q.
    The function enumerates all possible edge-failure states.
    """
    _validate_graph(graph)

    if (
        not isinstance(failure_probability, Real)
        or isinstance(failure_probability, bool)
        or not 0.0 <= failure_probability <= 1.0
    ):
        raise ValueError("failure_probability must be in [0, 1].")

    edges = list(graph.edges())
    m = len(edges)
    reliability = 0.0

    for mask in range(1 << m):
        failed_count = mask.bit_count()
        operational_count = m - failed_count

        state_probability = (
            failure_probability ** failed_count
            * (1.0 - failure_probability) ** operational_count
        )

        if state_probability == 0.0:
            continue

        operational_graph = graph.copy()

        failed_edges = [
            edges[index]
            for index in range(m)
            if mask & (1 << index)
        ]

        operational_graph.remove_edges_from(failed_edges)

        if nx.is_connected(operational_graph):
            reliability += state_probability

    return reliability


def all_terminal_average_reliability_exact(graph):
    """
    Compute the exact average all-terminal reliability.

    Average reliability is the integral of R(q) from q=0 to q=1.

    This implementation enumerates all edge-failure states and
    integrates each state's probability analytically.
    """
    _validate_graph(graph)

    edges = list(graph.edges())
    m = len(edges)
    average_reliability = 0.0

    for mask in range(1 << m):
        failed_count = mask.bit_count()

        operational_graph = graph.copy()

        failed_edges = [
            edges[index]
            for index in range(m)
            if mask & (1 << index)
        ]

        operational_graph.remove_edges_from(failed_edges)

        if nx.is_connected(operational_graph):
            state_integral = 1.0 / (
                (m + 1) * comb(m, failed_count)
            )
            average_reliability += state_integral

    return average_reliability
