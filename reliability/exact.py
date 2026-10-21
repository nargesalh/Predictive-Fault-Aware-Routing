
from numbers import Real

import networkx as nx


def all_terminal_reliability_exact(graph, failure_probability):
    """
    Compute exact all-terminal reliability for an undirected graph.

    Each edge fails independently with the same probability q.

    Parameters
    ----------
    graph : networkx.Graph
        The network whose reliability is being calculated.
    failure_probability : float
        Probability q that any individual edge fails, in [0, 1].

    Returns
    -------
    float
        Probability that all vertices remain connected.

    Notes
    -----
    This algorithm enumerates all 2^m possible edge-failure states.
    It is intended for small graphs.
    """
    if not isinstance(graph, nx.Graph):
        raise TypeError("graph must be a NetworkX graph.")

    if graph.is_directed():
        raise ValueError("Only undirected graphs are supported.")

    if graph.is_multigraph():
        raise ValueError("Parallel edges are not supported.")

    if graph.number_of_nodes() == 0:
        raise ValueError("graph must contain at least one node.")

    if (
        not isinstance(failure_probability, Real)
        or isinstance(failure_probability, bool)
        or not 0.0 <= failure_probability <= 1.0
    ):
        raise ValueError("failure_probability must be in [0, 1].")

    edges = list(graph.edges())
    number_of_edges = len(edges)

    reliability = 0.0

    # Enumerate every possible subset of failed edges.
    for mask in range(1 << number_of_edges):
        failed_count = mask.bit_count()
        operational_count = number_of_edges - failed_count

        # Probability of this particular edge-failure state.
        state_probability = (
            failure_probability ** failed_count
            * (1.0 - failure_probability) ** operational_count
        )

        # States with zero probability cannot contribute to reliability.
        if state_probability == 0.0:
            continue

        operational_graph = graph.copy()

        failed_edges = [
            edges[index]
            for index in range(number_of_edges)
            if mask & (1 << index)
        ]

        operational_graph.remove_edges_from(failed_edges)

        # All-terminal success means every vertex remains connected.
        if nx.is_connected(operational_graph):
            reliability += state_probability

    return reliability
