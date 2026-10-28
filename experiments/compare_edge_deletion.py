import csv
from pathlib import Path
from statistics import mean, median, stdev
from time import perf_counter

from experiments.compare_approximations import build_benchmark_graphs
from reliability import (
    all_terminal_average_reliability_exact,
    estimate_average_reliability,
)


TRIAL_COUNTS = (100, 500, 1000, 2500)
SEEDS = (42, 43, 44, 45, 46)


def run_benchmark(trial_counts=TRIAL_COUNTS, seeds=SEEDS):
    """Compare edge-deletion estimates with exact average reliability."""
    trial_counts = tuple(trial_counts)
    seeds = tuple(seeds)

    if not trial_counts or any(
        not isinstance(count, int)
        or isinstance(count, bool)
        or count <= 0
        for count in trial_counts
    ):
        raise ValueError("trial_counts must contain positive integers.")

    if not seeds or any(
        not isinstance(seed, int) or isinstance(seed, bool)
        for seed in seeds
    ):
        raise ValueError("seeds must contain integers.")

    rows = []

    for graph_name, graph in build_benchmark_graphs().items():
        start = perf_counter()
        exact = all_terminal_average_reliability_exact(graph)
        exact_runtime_ms = (perf_counter() - start) * 1000

        for trials in trial_counts:
            for seed in seeds:
                start = perf_counter()
                estimate = estimate_average_reliability(
                    graph,
                    trials=trials,
                    seed=seed,
                )
                runtime_ms = (perf_counter() - start) * 1000

                absolute_error = abs(estimate - exact)
                relative_error = (
                    absolute_error / abs(exact)
                    if exact != 0
                    else None
                )

                rows.append(
                    {
                        "graph_name": graph_name,
                        "num_nodes": graph.number_of_nodes(),
                        "num_edges": graph.number_of_edges(),
                        "trials": trials,
                        "seed": seed,
                        "exact_average_reliability": exact,
                        "estimate": estimate,
                        "absolute_error": absolute_error,
                        "relative_error": relative_error,
                        "exact_runtime_ms": exact_runtime_ms,
                        "runtime_ms": runtime_ms,
                    }
                )

    return rows


def save_results_csv(rows, output_path):
    """Save individual benchmark runs to CSV."""
    if not rows:
        raise ValueError("Cannot save empty benchmark results.")

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


def print_summary(rows):
    """Print error, variability, and runtime by graph and trial count."""
    print("\n=== Edge deletion benchmark ===")
    print(f"Number of runs: {len(rows)}")

    graph_names = dict.fromkeys(
        row["graph_name"] for row in rows
    )

    for graph_name in graph_names:
        graph_rows = [
            row for row in rows
            if row["graph_name"] == graph_name
        ]

        exact = graph_rows[0]["exact_average_reliability"]
        print(
            f"\n{graph_name}: "
            f"exact average reliability = {exact:.6f}"
        )

        trial_counts = sorted(
            {row["trials"] for row in graph_rows}
        )

        for trials in trial_counts:
            selected = [
                row for row in graph_rows
                if row["trials"] == trials
            ]

            estimates = [row["estimate"] for row in selected]
            errors = [row["absolute_error"] for row in selected]
            runtimes = [row["runtime_ms"] for row in selected]

            print(
                f"  trials={trials:4d}: "
                f"mean absolute error={mean(errors):.6f} | "
                f"estimate std={stdev(estimates):.6f} | "
                f"median runtime={median(runtimes):.3f} ms"
            )


def main():
    output_path = Path("outputs") / "edge_deletion_benchmark.csv"
    rows = run_benchmark()

    save_results_csv(rows, output_path)
    print_summary(rows)
    print("\nResults saved to:", output_path.resolve())


if __name__ == "__main__":
    main()