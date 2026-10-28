import networkx as nx
import pytest

from experiments.topology_features import extract_topology_features


def test_path_graph_features():
    features = extract_topology_features(nx.path_graph(5))

    assert features["num_nodes"] == 5
    assert features["num_edges"] == 4
    assert features["density"] == pytest.approx(0.4)
    assert features["average_degree"] == pytest.approx(1.6)
    assert features["degree_1_fraction"] == pytest.approx(0.4)
    assert features["degree_2_fraction"] == pytest.approx(0.6)
    assert features["num_bridges"] == 4
    assert features["num_articulation_points"] == 3
    assert features["cycle_rank"] == 0


def test_cycle_graph_features():
    features = extract_topology_features(nx.cycle_graph(5))

    assert features["num_bridges"] == 0
    assert features["num_articulation_points"] == 0
    assert features["degree_2_fraction"] == pytest.approx(1.0)
    assert features["cycle_rank"] == 1


def test_complete_graph_features():
    features = extract_topology_features(nx.complete_graph(4))

    assert features["density"] == pytest.approx(1.0)
    assert features["average_clustering"] == pytest.approx(1.0)
    assert features["degree_3_plus_fraction"] == pytest.approx(1.0)
    assert features["cycle_rank"] == 3


def test_empty_graph_is_rejected():
    with pytest.raises(ValueError, match="at least one node"):
        extract_topology_features(nx.Graph())


def test_directed_graph_is_rejected():
    with pytest.raises(ValueError, match="Directed"):
        extract_topology_features(nx.DiGraph([(1, 2)]))


def test_multigraph_is_rejected():
    with pytest.raises(ValueError, match="Multigraphs"):
        extract_topology_features(nx.MultiGraph([(1, 2)]))