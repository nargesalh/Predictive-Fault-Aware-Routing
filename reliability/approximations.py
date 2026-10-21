
import math
from numbers import Real

import networkx as nx


def _validate_approximation_input(graph, failure_probability):
    """Validate graph structure and edge failure probability."""
    if not isinstance(graph, nx.Graph):
        raise TypeError("graph must be a NetworkX graph.")

    if graph.is_directed():
        raise ValueError("Only undirected graphs are supported.")

    if graph.is_multigraph():
        raise ValueError("Parallel edges are not supported.")

    if graph.number_of_nodes() < 2:
        raise ValueError("graph must contain at least two nodes.")

    if nx.number_of_selfloops(graph) > 0:
        raise ValueError("Self-loops are not supported.")

    if not nx.is_connected(graph):
        raise ValueError("graph must be connected.")

    if (
        not isinstance(failure_probability, Real)
        or isinstance(failure_probability, bool)
        or not math.isfinite(failure_probability)
        or not 0.0 <= failure_probability <= 1.0
    ):
        raise ValueError("failure_probability must be in [0, 1].")


def first_order_approximation(graph, failure_probability):
    """
    Estimate all-terminal reliability using the first-order approximation.

    R1(q) = product over vertices v of (1 - q ** degree(v)).
    """
    _validate_approximation_input(graph, failure_probability)

    q = failure_probability

    # A connected network with at least two nodes is fully operational
    # when q=0 and fully disconnected when q=1.
    if q == 0.0:
        return 1.0

    if q == 1.0:
        return 0.0

    node_factors = [
        1.0 - q ** degree
        for _, degree in graph.degree()
    ]

    return math.prod(node_factors)


def second_order_approximation(graph, failure_probability):
    """
    Estimate all-terminal reliability using the second-order approximation.

    R2(q) includes vertex-isolation factors and edge-related factors.
    """
    _validate_approximation_input(graph, failure_probability)

    q = failure_probability

    if q == 0.0:
        return 1.0

    if q == 1.0:
        return 0.0

    degrees = dict(graph.degree())

    # First-order contribution from isolated vertices.
    result = first_order_approximation(graph, q)

    # Additional correction terms for edge-related disconnections.
    for u, v in graph.edges():
        degree_sum = degrees[u] + degrees[v]

        edge_factor = (
            1.0 - q ** (degree_sum - 2) * (1.0 - q)
        )

        result *= edge_factor

    return result
