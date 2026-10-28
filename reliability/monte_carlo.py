
import random
from math import isfinite
from numbers import Real

import networkx as nx


def estimate_all_terminal_reliability_monte_carlo(
    graph,
    failure_probability,
    trials=10_000,
    seed=42,
):
    """
    Estimate all-terminal reliability by Monte Carlo sampling.

    Each edge fails independently with the same failure probability.
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
        or not isfinite(failure_probability)
        or not 0.0 <= failure_probability <= 1.0
    ):
        raise ValueError(
            "failure_probability must be finite and in [0, 1]."
        )

    if (
        not isinstance(trials, int)
        or isinstance(trials, bool)
        or trials <= 0
    ):
        raise ValueError("trials must be a positive integer.")

    rng = random.Random(seed)
    edges = list(graph.edges())
    successful_trials = 0

    for _ in range(trials):
        operational_graph = graph.copy()

        failed_edges = [
            edge
            for edge in edges
            if rng.random() < failure_probability
        ]

        operational_graph.remove_edges_from(failed_edges)

        if nx.is_connected(operational_graph):
            successful_trials += 1

    return successful_trials / trials
