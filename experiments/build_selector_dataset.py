
import csv
from pathlib import Path

from experiments.compare_approximations import build_benchmark_graphs
from experiments.topology_features import extract_topology_features


ALGORITHMS = (
    ("exact", "exact_reliability", None, None),
    ("r1", "r1_estimate", "r1_absolute_error", "r1_relative_error"),
    ("r2", "r2_estimate", "r2_absolute_error", "r2_relative_error"),
    ("rs", "rs_estimate", "rs_absolute_error", "rs_relative_error"),
    ("mc", "mc_estimate", "mc_absolute_error", "mc_relative_error"),
)


def _optional_float(value):
    """Convert a non-empty CSV value to float."""
    if value is None or value == "":
        return None

    return float(value)


def build_selector_rows(benchmark_rows, graphs):
    """Combine topology features with algorithm accuracy results."""
    if not benchmark_rows:
        raise ValueError("Benchmark results must not be empty.")

    features_by_graph = {
        name: extract_topology_features(graph)
        for name, graph in graphs.items()
    }

    selector_rows = []

    for benchmark_row in benchmark_rows:
        graph_name = benchmark_row["graph_name"]

        if graph_name not in features_by_graph:
            raise ValueError(
                f"Unknown benchmark graph: {graph_name}"
            )

        graph_features = features_by_graph[graph_name]
        exact = float(benchmark_row["exact_reliability"])
        failure_probability = float(
            benchmark_row["failure_probability"]
        )

        for algorithm, estimate_key, abs_key, rel_key in ALGORITHMS:
            estimate = _optional_float(
                benchmark_row.get(estimate_key)
            )

            if algorithm == "exact":
                estimate = exact
                absolute_error = 0.0
                relative_error = 0.0 if exact != 0 else None
            elif estimate is None:
                absolute_error = None
                relative_error = None
            else:
                absolute_error = _optional_float(
                    benchmark_row.get(abs_key)
                )
                relative_error = _optional_float(
                    benchmark_row.get(rel_key)
                )

            selector_rows.append(
                {
                    "graph_name": graph_name,
                    "failure_probability": failure_probability,
                    "algorithm": algorithm,
                    "is_applicable": estimate is not None,
                    **graph_features,
                    "exact_reliability": exact,
                    "estimate": estimate,
                    "absolute_error": absolute_error,
                    "relative_error": relative_error,
                }
            )

    return selector_rows


def save_dataset(rows, output_path):
    """Save the selector dataset as CSV."""
    if not rows:
        raise ValueError("Cannot save an empty dataset.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    input_path = Path("outputs") / "reliability_benchmark.csv"
    output_path = Path("outputs") / "selector_accuracy_dataset.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            "Benchmark CSV not found. Run "
            "'python -m experiments.compare_approximations' first."
        )

    with input_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        benchmark_rows = list(csv.DictReader(csv_file))

    graphs = build_benchmark_graphs()
    selector_rows = build_selector_rows(benchmark_rows, graphs)
    save_dataset(selector_rows, output_path)

    print("Benchmark cases:", len(benchmark_rows))
    print("Selector dataset rows:", len(selector_rows))
    print("Output saved to:", output_path.resolve())


if __name__ == "__main__":
    main()
