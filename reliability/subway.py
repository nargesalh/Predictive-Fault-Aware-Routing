
import math
from numbers import Real

import networkx as nx


class SubwayApproximationNotApplicable(ValueError):
    """Raised when a graph is outside the supported Rs approximation class."""


def _validate_input(graph, failure_probability):
    """Validate a graph and its common edge-failure probability."""
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


def _remove_one_shell(graph):
    """
    Repeatedly remove degree-one vertices.

    Returns the remaining graph and the number of removed edges.
    Every removed edge must work for the original network to remain
    fully connected.
    """
    core = graph.copy()
    removed_edges = 0

    while True:
        leaves = [
            node
            for node, degree in core.degree()
            if degree == 1
        ]

        if not leaves:
            break

        edges_before = core.number_of_edges()
        core.remove_nodes_from(leaves)
        removed_edges += edges_before - core.number_of_edges()

    return core, removed_edges


def _extract_degree_two_path_lengths(core):
    """
    Extract lengths of maximal paths between junction vertices.

    Junctions are vertices whose degree is not two. All internal
    vertices of each extracted path must have degree two.

    Returns:
        (path_lengths, core_type)

    core_type is one of:
        "empty", "cycle", "paths"
    """
    if core.number_of_edges() == 0:
        return [], "empty"

    # A connected graph in which every vertex has degree two is a cycle.
    if all(degree == 2 for _, degree in core.degree()):
        return [core.number_of_edges()], "cycle"

    junctions = {
        node
        for node, degree in core.degree()
        if degree != 2
    }

    if not junctions:
        raise SubwayApproximationNotApplicable(
            "Could not identify junction vertices."
        )

    visited_edges = set()
    path_lengths = []

    for start in junctions:
        for neighbor in core.neighbors(start):
            first_edge = frozenset((start, neighbor))

            if first_edge in visited_edges:
                continue

            visited_edges.add(first_edge)
            length = 1
            previous = start
            current = neighbor

            # Follow degree-two vertices until another junction is reached.
            while current not in junctions:
                candidates = [
                    node
                    for node in core.neighbors(current)
                    if node != previous
                ]

                if len(candidates) != 1:
                    raise SubwayApproximationNotApplicable(
                        "Could not decompose the degree-two paths."
                    )

                next_node = candidates[0]
                next_edge = frozenset((current, next_node))

                if next_edge in visited_edges:
                    raise SubwayApproximationNotApplicable(
                        "Unexpected cycle while extracting paths."
                    )

                visited_edges.add(next_edge)
                previous, current = current, next_node
                length += 1

            # A direct junction-to-junction edge has length one.
            # The Rs approximation used here is not applied to such graphs.
            if length < 2:
                raise SubwayApproximationNotApplicable(
                    "Rs requires junction-to-junction paths "
                    "with at least one internal degree-two vertex."
                )

            path_lengths.append(length)

    if len(visited_edges) != core.number_of_edges():
        raise SubwayApproximationNotApplicable(
            "Not all core edges could be assigned to paths."
        )

    return path_lengths, "paths"


def subway_type_approximation(graph, failure_probability):
    """
    Estimate all-terminal reliability using the subway-type approximation.

    The graph is first reduced by repeatedly removing degree-one vertices.
    The removed edges contribute a factor (1-q)^K.

    For each remaining degree-two path of length l, use the paper's factor:

        (1-q)^l + l*q*(1-q)^(l-1)

    The product of these factors approximates reliability for
    suitable subway-like network structures.

    Trees and simple cycles are handled separately using their
    exact reliability expressions.
    """
    _validate_input(graph, failure_probability)

    q = failure_probability
    p = 1.0 - q

    core, removed_edges = _remove_one_shell(graph)

    path_lengths, core_type = _extract_degree_two_path_lengths(core)

    # All edges were removed by one-shell reduction.
    # For a tree, every original edge must work.
    if core_type == "empty":
        return p ** removed_edges

    # Each removed leaf edge must work.
    result = p ** removed_edges

    # For a cycle, the same path factor is exact:
    # the cycle stays connected if at most one edge fails.
    for length in path_lengths:
        path_factor = (
            p ** length
            + length * q * p ** (length - 1)
        )
        result *= path_factor

    return result
