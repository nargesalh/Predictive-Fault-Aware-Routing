
import networkx as nx
import pytest

from experiments.build_selector_dataset import build_selector_rows


def make_benchmark_row():
    return {
        "graph_name": "path_3",
        "failure_probability": "0.1",
        "exact_reliability": "0.81",
        "r1_estimate": "0.80",
        "r2_estimate": "0.805",
        "rs_estimate": "",
        "r1_absolute_error": "0.01",
        "r2_absolute_error": "0.005",
        "rs_absolute_error": "",
        "r1_relative_error": "0.012345679",
        "r2_relative_error": "0.006172840",
        "rs_relative_error": "",
    }


def test_build_selector_rows_creates_four_candidates():
    rows = build_selector_rows(
        [make_benchmark_row()],
        {"path_3": nx.path_graph(3)},
    )

    assert len(rows) == 4
    assert {row["algorithm"] for row in rows} == {
        "exact", "r1", "r2", "rs"
    }


def test_exact_is_the_reference_candidate():
    rows = build_selector_rows(
        [make_benchmark_row()],
        {"path_3": nx.path_graph(3)},
    )

    exact_row = next(
        row for row in rows if row["algorithm"] == "exact"
    )

    assert exact_row["estimate"] == pytest.approx(0.81)
    assert exact_row["absolute_error"] == 0.0
    assert exact_row["is_applicable"] is True


def test_inapplicable_algorithm_is_preserved():
    rows = build_selector_rows(
        [make_benchmark_row()],
        {"path_3": nx.path_graph(3)},
    )

    rs_row = next(
        row for row in rows if row["algorithm"] == "rs"
    )

    assert rs_row["is_applicable"] is False
    assert rs_row["estimate"] is None
    assert rs_row["absolute_error"] is None


def test_unknown_graph_is_rejected():
    with pytest.raises(ValueError, match="Unknown benchmark graph"):
        build_selector_rows(
            [make_benchmark_row()],
            {"another_graph": nx.path_graph(3)},
        )


def test_empty_benchmark_is_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        build_selector_rows([], {})
