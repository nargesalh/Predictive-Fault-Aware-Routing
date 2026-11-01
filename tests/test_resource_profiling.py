import csv
import sys
import types
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments import profile_algorithm_resources as prof

CONFIG = {"timing_repeats": 5, "memory_repeats": 2, "mc_trials": 200, "mc_seed": 7}


def small_graphs():
    return {"cycle_5": nx.cycle_graph(5), "complete_4": nx.complete_graph(4)}


def run_reference(graphs=None, probabilities=(0.1, 0.3), config=CONFIG):
    graphs = graphs or small_graphs()
    return prof.run_profiling(
        graphs, list(probabilities), ["exact", "mc"], prof.reference_registry(), config
    )


def test_output_for_supported_algorithms():
    summary, raw = run_reference()
    assert len(summary) == 2 * 2 * 2
    assert {r["algorithm"] for r in summary} == {"exact", "mc"}
    assert all(r["status"] == "ok" for r in summary)
    assert len(raw) == len(summary) * (CONFIG["timing_repeats"] + CONFIG["memory_repeats"])


def test_time_and_memory_are_valid():
    summary, raw = run_reference()
    for row in summary:
        assert row["runtime_median_ms"] > 0
        assert row["runtime_iqr_ms"] >= 0
        assert row["peak_python_memory_median_mb"] > 0
    assert all(r["value"] > 0 for r in raw)


def make_fake_package(monkeypatch, calls):
    fake = types.ModuleType("reliability")

    class SubwayApproximationNotApplicable(Exception):
        pass

    def exact(graph, p):
        calls.append(("exact", p))
        return 0.5

    def first(graph, p):
        calls.append(("r1", p))
        return 0.4

    def second(graph, p):
        calls.append(("r2", p))
        return 0.45

    def subway(graph, p):
        raise SubwayApproximationNotApplicable("core has bridges")

    def mc(graph, p, trials=10, seed=1):
        calls.append(("mc", trials, seed))
        return 0.48

    fake.all_terminal_reliability_exact = exact
    fake.first_order_approximation = first
    fake.second_order_approximation = second
    fake.subway_type_approximation = subway
    fake.estimate_all_terminal_reliability_monte_carlo = mc
    fake.SubwayApproximationNotApplicable = SubwayApproximationNotApplicable
    monkeypatch.setitem(sys.modules, "reliability", fake)


def test_project_registry_calls_real_function_names(monkeypatch):
    calls = []
    make_fake_package(monkeypatch, calls)
    registry = prof.project_registry()
    summary, _ = prof.run_profiling(
        {"cycle_5": nx.cycle_graph(5)}, [0.1], ["exact", "r1", "r2", "mc"], registry, CONFIG
    )
    assert all(r["status"] == "ok" for r in summary)
    assert ("mc", CONFIG["mc_trials"], CONFIG["mc_seed"]) in calls
    assert ("exact", 0.1) in calls


def test_rs_not_applicable_is_recorded_not_failed(monkeypatch):
    make_fake_package(monkeypatch, [])
    registry = prof.project_registry()
    summary, raw = prof.profile_combination("path_6", nx.path_graph(6), 0.1, registry["rs"], CONFIG)
    assert summary["status"] == "not_applicable"
    assert "SubwayApproximationNotApplicable" in summary["reason"]
    assert summary["runtime_median_ms"] == ""
    assert summary["peak_python_memory_median_mb"] == ""
    assert raw == []


def test_unavailable_when_package_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "reliability", None)
    registry = prof.project_registry()
    summary, raw = prof.profile_combination("cycle_5", nx.cycle_graph(5), 0.1, registry["r1"], CONFIG)
    assert summary["status"] == "unavailable"
    assert raw == []


def test_project_topologies_dict_and_list(monkeypatch):
    fake = types.ModuleType("experiments.compare_approximations")
    fake.build_benchmark_graphs = lambda: {"a": nx.path_graph(3)}
    monkeypatch.setitem(sys.modules, "experiments.compare_approximations", fake)
    assert list(prof.project_topologies()) == ["a"]
    fake.build_benchmark_graphs = lambda: [("b", nx.path_graph(3))]
    assert list(prof.project_topologies()) == ["b"]
    fake.build_benchmark_graphs = lambda: [nx.path_graph(3)]
    with pytest.raises(ValueError):
        prof.project_topologies()


def test_reproducible_settings_and_results():
    first_summary, first_raw = run_reference()
    second_summary, second_raw = run_reference()
    keys = ["graph_name", "num_nodes", "num_edges", "failure_probability", "algorithm",
            "mc_trials", "mc_seed", "status", "timing_repeats", "memory_repeats"]
    assert [[r[k] for k in keys] for r in first_summary] == [[r[k] for k in keys] for r in second_summary]
    assert [r["result_value"] for r in first_raw] == [r["result_value"] for r in second_raw]


def test_mc_fields_empty_for_other_algorithms():
    summary, _ = run_reference()
    for row in summary:
        if row["algorithm"] == "mc":
            assert row["mc_trials"] == CONFIG["mc_trials"]
            assert row["mc_seed"] == CONFIG["mc_seed"]
        else:
            assert row["mc_trials"] == ""
            assert row["mc_seed"] == ""


def test_csv_saved_correctly(tmp_path):
    summary, raw = run_reference()
    summary_path = tmp_path / "summary.csv"
    raw_path = tmp_path / "raw.csv"
    prof.write_csv(summary_path, prof.SUMMARY_FIELDS, summary)
    prof.write_csv(raw_path, prof.RAW_FIELDS, raw)
    with open(summary_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        assert list(rows[0].keys()) == prof.SUMMARY_FIELDS
    assert len(rows) == len(summary)
    with open(raw_path, newline="", encoding="utf-8") as handle:
        raw_rows = list(csv.DictReader(handle))
        assert list(raw_rows[0].keys()) == prof.RAW_FIELDS
    assert len(raw_rows) == len(raw)


@pytest.mark.parametrize("bad", [0, 1, -0.5, 1.5, "0.1", None, True])
def test_invalid_probability_rejected(bad):
    with pytest.raises(ValueError):
        prof.run_profiling(small_graphs(), [bad], ["exact"], prof.reference_registry(), CONFIG)


def test_unknown_algorithm_rejected():
    with pytest.raises(ValueError):
        prof.run_profiling(small_graphs(), [0.1], ["nope"], prof.reference_registry(), CONFIG)


def test_invalid_config_rejected():
    bad = dict(CONFIG, timing_repeats=2)
    with pytest.raises(ValueError):
        prof.run_profiling(small_graphs(), [0.1], ["exact"], prof.reference_registry(), bad)


def test_failing_algorithm_is_recorded():
    def boom(graph, p):
        raise RuntimeError("broken")

    algo = prof.Algorithm("boom", boom, False, prof.always_applicable)
    summary, raw = prof.profile_combination("cycle_5", nx.cycle_graph(5), 0.1, algo, CONFIG)
    assert summary["status"] == "failed"
    assert "RuntimeError" in summary["reason"]
    assert summary["runtime_median_ms"] == ""
    assert raw == []


def test_graph_unchanged_by_measurement():
    graph = nx.complete_graph(4)
    before = prof.graph_signature(graph)
    for algo in prof.reference_registry().values():
        prof.profile_combination("complete_4", graph, 0.2, algo, CONFIG)
    assert prof.graph_signature(graph) == before


def test_graph_modifying_algorithm_is_flagged():
    def mutate(graph, p):
        graph.add_edge("x", "y")
        return 0.5

    algo = prof.Algorithm("mutate", mutate, False, prof.always_applicable)
    summary, _ = prof.profile_combination("cycle_5", nx.cycle_graph(5), 0.1, algo, CONFIG)
    assert summary["status"] == "failed"
    assert summary["reason"] == "graph_modified"


def test_exact_matches_known_value():
    graph = nx.path_graph(3)
    assert prof.reference_exact(graph, 0.1) == pytest.approx(0.81)


def test_sample_run_on_small_topologies(tmp_path):
    code = prof.main([
        "--source", "reference",
        "--algorithms", "exact", "mc",
        "--graphs", "cycle_8", "path_8",
        "--probabilities", "0.1", "0.3",
        "--mc-trials", "200",
        "--output-dir", str(tmp_path),
    ])
    assert code == 0
    assert (tmp_path / "resource_profile_raw.csv").exists()
    assert (tmp_path / "resource_profile_summary.csv").exists()
