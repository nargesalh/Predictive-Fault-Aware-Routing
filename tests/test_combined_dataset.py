import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments import build_combined_dataset as comb
from experiments import profile_edge_deletion_resources as ed


def acc(graph="path_5", p="0.1", algo="r1", applicable="True"):
    return {"graph_name": graph, "failure_probability": p, "algorithm": algo,
            "is_applicable": applicable, "num_nodes": "5", "absolute_error": "0.01"}


def res(graph="path_5", p="0.1", algo="r1", status="ok"):
    row = {c: "" for c in comb.RESOURCE_COLUMNS}
    row.update({"graph_name": graph, "failure_probability": p, "algorithm": algo,
                "status": status, "reason": "", "runtime_median_ms": "0.5"})
    return row


def test_topology_type():
    assert comb.topology_type("path_5") == "path"
    assert comb.topology_type("random_3_regular_6") == "random_regular"
    assert comb.topology_type("grid_3x3") == "grid"
    assert comb.topology_type("subway_like_small") == "subway_like_small"


def test_combine_joins_and_adds_ids():
    rows = comb.combine([acc(), acc(algo="rs", applicable="False")],
                        [res(), res(algo="rs", status="not_applicable")])
    assert [r["experiment_id"] for r in rows] == ["exp_0001", "exp_0002"]
    assert rows[0]["runtime_median_ms"] == "0.5"
    assert {r["resource_status"] for r in rows} == {"ok", "not_applicable"}


def test_combine_float_format_does_not_break_key():
    rows = comb.combine([acc(p="0.10")], [res(p="0.1")])
    assert len(rows) == 1


def test_combine_rejects_key_mismatch():
    with pytest.raises(ValueError, match="Keys differ"):
        comb.combine([acc()], [res(algo="r2")])


def test_combine_rejects_applicability_mismatch():
    with pytest.raises(ValueError, match="Applicability"):
        comb.combine([acc(applicable="False")], [res()])


def test_combine_rejects_duplicates_and_empty():
    with pytest.raises(ValueError):
        comb.combine([acc(), acc()], [res()])
    with pytest.raises(ValueError):
        comb.combine([], [res()])


def test_edge_deletion_profile_runs_and_keeps_graph():
    graph = nx.cycle_graph(5)
    before = sorted(graph.edges())
    rows = ed.profile_edge_deletion({"cycle_5": graph}, trial_counts=(50, 100),
                                    timing_repeats=5, memory_repeats=1)
    assert [r["algorithm"] for r in rows] == ["exact_average", "edge_deletion", "edge_deletion"]
    assert all(r["status"] == "ok" and r["runtime_median_ms"] > 0 for r in rows)
    assert sorted(graph.edges()) == before


def test_edge_deletion_rejects_bad_repeats():
    with pytest.raises(ValueError):
        ed.profile_edge_deletion({"c": nx.cycle_graph(4)}, timing_repeats=2)
