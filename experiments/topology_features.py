from statistics import pstdev

import networkx as nx


def extract_topology_features(graph):
    """Extract structural features from an undirected graph."""
    if not isinstance(graph, nx.Graph):
        raise TypeError("graph must be a NetworkX graph.")

    if graph.is_directed():
        raise ValueError("Directed graphs are not supported.")

    if graph.is_multigraph():
        raise ValueError("Multigraphs are not supported.")

    if graph.number_of_nodes() == 0:
        raise ValueError("graph must contain at least one node.")

    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    degrees = [degree for _, degree in graph.degree()]
    num_components = nx.number_connected_components(graph)

    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "density": nx.density(graph),
        "average_degree": sum(degrees) / num_nodes,
        "min_degree": min(degrees),
        "max_degree": max(degrees),
        "degree_std": pstdev(degrees),
        "degree_0_fraction": sum(d == 0 for d in degrees) / num_nodes,
        "degree_1_fraction": sum(d == 1 for d in degrees) / num_nodes,
        "degree_2_fraction": sum(d == 2 for d in degrees) / num_nodes,
        "degree_3_plus_fraction": sum(d >= 3 for d in degrees) / num_nodes,
        "average_clustering": nx.average_clustering(graph),
        "num_bridges": sum(1 for _ in nx.bridges(graph)),
        "num_articulation_points": sum(
            1 for _ in nx.articulation_points(graph)
        ),
        "num_connected_components": num_components,
        "cycle_rank": num_edges - num_nodes + num_components,
    }