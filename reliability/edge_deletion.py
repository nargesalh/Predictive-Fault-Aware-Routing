
import random

import networkx as nx


def _validate_connected_graph(graph):
    """Validate input for the edge deletion process."""
    if not isinstance(graph, nx.Graph):
        raise TypeError("graph must be a NetworkX graph.")

    if graph.is_directed():
        raise ValueError("Only undirected graphs are supported.")

    if graph.is_multigraph():
        raise ValueError("Parallel edges are not supported.")

    if graph.number_of_nodes() < 2:
        raise ValueError("graph must contain at least two nodes.")

    if not nx.is_connected(graph):
        raise ValueError("graph must initially be connected.")


def _simulate_one_deletion_process(graph, rng):
    """Delete randomly ordered edges until the graph disconnects."""
    edges = list(graph.edges())
    rng.shuffle(edges)

    remaining_graph = graph.copy()

    for deleted_count, edge in enumerate(edges, start=1):
        remaining_graph.remove_edge(*edge)

        if not nx.is_connected(remaining_graph):
            return deleted_count

    # A connected graph with at least two nodes must disconnect
    # after all its edges have been removed.
    raise RuntimeError("The graph did not become disconnected.")


def sample_edge_deletion_counts(graph, trials=1000, seed=42):
    """
    Run repeated edge deletion experiments.

    Returns a list containing the number of edges removed
    before disconnection in each trial.
    """
    _validate_connected_graph(graph)

    if (
        not isinstance(trials, int)
        or isinstance(trials, bool)
        or trials <= 0
    ):
        raise ValueError("trials must be a positive integer.")

    rng = random.Random(seed)

    return [
        _simulate_one_deletion_process(graph, rng)
        for _ in range(trials)
    ]


def estimate_average_reliability(graph, trials=1000, seed=42):
    """
    Estimate average all-terminal reliability using edge deletion.

    The estimator is mean(K) / (m + 1), where K is the number
    of edges removed before the graph becomes disconnected.
    """
    deletion_counts = sample_edge_deletion_counts(
        graph,
        trials=trials,
        seed=seed,
    )

    mean_deleted_edges = sum(deletion_counts) / len(deletion_counts)
    m = graph.number_of_edges()

    return mean_deleted_edges / (m + 1)
