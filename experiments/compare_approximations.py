
import csv
import math
from pathlib import Path
from statistics import mean, median
from time import perf_counter

import matplotlib.pyplot as plt
import networkx as nx

from reliability import (
    SubwayApproximationNotApplicable,
    all_terminal_reliability_exact,
    first_order_approximation,
    second_order_approximation,
    subway_type_approximation,
)


DEFAULT_Q_VALUES = (
    0.01,
    0.05,
    0.10,
    0.20,
    0.30,
    0.50,
    0.70,
    0.90,
    0.99,
)


def build_subway_like_graph():
    """
    Build a small sparse subway-like graph.

    A K4 graph with one edge removed is used as the junction skeleton.
    Every skeleton edge is replaced by a path of length two.

    The resulting graph has two degree-three junctions and
    three paths between them, of lengths 2, 4, and 4.
    """
    core = nx.complete_graph(4)
    core.remove_edge(0, 1)

    graph = nx.Graph()
    graph.add_nodes_from(core.nodes())

    for u, v in core.edges():
        intermediate = f"mid_{u}_{v}"
        graph.add_edge(u, intermediate)
        graph.add_edge(intermediate, v)

    return graph


def build_benchmark_graphs():
    """Create connected graph families for reliability benchmarking."""
    graphs = {
        "path_5": nx.path_graph(5),
        "cycle_5": nx.cycle_graph(5),
        "complete_4": nx.complete_graph(4),
        "random_3_regular_6": nx.random_regular_graph(
            3, 6, seed=42
        ),
        "subway_like_small": build_subway_like_graph(),
    }

    for name, graph in graphs.items():
        if not nx.is_connected(graph):
            raise ValueError(
                f"Benchmark graph '{name}' must be connected."
            )

    return graphs


def _measure_runtime_ms(function, repeats):
    """Return the last result and median runtime in milliseconds."""
    timings = []
    result = None

    for _ in range(repeats):
        start = perf_counter()
        result = function()
        elapsed_ms = (perf_counter() - start) * 1000.0
        timings.append(elapsed_ms)

    return result, median(timings)


def _relative_error(estimate, exact):
    """Calculate relative error, or None when the exact value is zero."""
    if exact == 0.0:
        return None

    return abs(estimate - exact) / abs(exact)


def run_benchmark(q_values=DEFAULT_Q_VALUES, repeats=3):
    """
    Compare exact, R1, R2, and Rs where each method is applicable.

    Rs is left empty for graph structures outside its supported class.
    """
    if (
        not isinstance(repeats, int)
        or isinstance(repeats, bool)
        or repeats <= 0
    ):
        raise ValueError("repeats must be a positive integer.")

    q_values = tuple(q_values)

    if not q_values:
        raise ValueError(
            "q_values must contain at least one failure probability."
        )

    for q in q_values:
        if (
            not isinstance(q, (int, float))
            or isinstance(q, bool)
            or not math.isfinite(q)
            or not 0.0 <= q <= 1.0
        ):
            raise ValueError(
                "Failure probabilities must be finite values in [0, 1]."
            )

    graphs = build_benchmark_graphs()
    rows = []

    for graph_name, graph in graphs.items():
        for q in q_values:
            exact, exact_ms = _measure_runtime_ms(
                lambda: all_terminal_reliability_exact(graph, q),
                repeats,
            )

            r1, r1_ms = _measure_runtime_ms(
                lambda: first_order_approximation(graph, q),
                repeats,
            )

            r2, r2_ms = _measure_runtime_ms(
                lambda: second_order_approximation(graph, q),
                repeats,
            )

            try:
                rs, rs_ms = _measure_runtime_ms(
                    lambda: subway_type_approximation(graph, q),
                    repeats,
                )

                rs_abs_error = abs(rs - exact)
                rs_rel_error = _relative_error(rs, exact)

            except SubwayApproximationNotApplicable:
                rs = None
                rs_ms = None
                rs_abs_error = None
                rs_rel_error = None

            rows.append(
                {
                    "graph_name": graph_name,
                    "num_nodes": graph.number_of_nodes(),
                    "num_edges": graph.number_of_edges(),
                    "failure_probability": q,
                    "exact_reliability": exact,
                    "r1_estimate": r1,
                    "r2_estimate": r2,
                    "rs_estimate": rs,
                    "r1_absolute_error": abs(r1 - exact),
                    "r2_absolute_error": abs(r2 - exact),
                    "rs_absolute_error": rs_abs_error,
                    "r1_relative_error": _relative_error(r1, exact),
                    "r2_relative_error": _relative_error(r2, exact),
                    "rs_relative_error": rs_rel_error,
                    "exact_runtime_ms": exact_ms,
                    "r1_runtime_ms": r1_ms,
                    "r2_runtime_ms": r2_ms,
                    "rs_runtime_ms": rs_ms,
                }
            )

    return rows


def save_results_csv(rows, output_path):
    """Save benchmark results as a CSV file."""
    if not rows:
        raise ValueError("Cannot save an empty benchmark result.")

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


def plot_reliability_curves(rows, output_path):
    """Plot exact reliability and applicable approximation curves."""
    graph_names = list(
        dict.fromkeys(row["graph_name"] for row in rows)
    )

    fig, axes = plt.subplots(3, 2, figsize=(13, 12), sharex=True)
    axes = axes.flatten()

    for ax, graph_name in zip(axes, graph_names):
        graph_rows = sorted(
            (
                row
                for row in rows
                if row["graph_name"] == graph_name
            ),
            key=lambda row: row["failure_probability"],
        )

        q_values = [
            row["failure_probability"] for row in graph_rows
        ]

        ax.plot(
            q_values,
            [row["exact_reliability"] for row in graph_rows],
            marker="o",
            label="Exact",
        )

        ax.plot(
            q_values,
            [row["r1_estimate"] for row in graph_rows],
            marker="s",
            linestyle="--",
            label="R1",
        )

        ax.plot(
            q_values,
            [row["r2_estimate"] for row in graph_rows],
            marker="^",
            linestyle=":",
            label="R2",
        )

        rs_rows = [
            row
            for row in graph_rows
            if row["rs_estimate"] is not None
        ]

        if rs_rows:
            ax.plot(
                [row["failure_probability"] for row in rs_rows],
                [row["rs_estimate"] for row in rs_rows],
                marker="D",
                linestyle="-.",
                label="Rs",
            )

        ax.set_title(graph_name)
        ax.set_xlabel("Edge failure probability q")
        ax.set_ylabel("All-terminal reliability")
        ax.set_ylim(-0.03, 1.03)
        ax.grid(True, alpha=0.3)
        ax.legend()

    for ax in axes[len(graph_names):]:
        ax.set_visible(False)

    fig.suptitle(
        "Exact vs Approximate Network Reliability",
        fontsize=15,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_average_absolute_error(rows, output_path):
    """Plot R1 and R2 mean absolute errors across all graph families."""
    q_values = sorted(
        {row["failure_probability"] for row in rows}
    )

    r1_errors = []
    r2_errors = []

    for q in q_values:
        selected_rows = [
            row
            for row in rows
            if row["failure_probability"] == q
        ]

        r1_errors.append(
            mean(row["r1_absolute_error"] for row in selected_rows)
        )

        r2_errors.append(
            mean(row["r2_absolute_error"] for row in selected_rows)
        )

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(
        q_values,
        r1_errors,
        marker="s",
        label="R1 mean absolute error",
    )

    ax.plot(
        q_values,
        r2_errors,
        marker="^",
        label="R2 mean absolute error",
    )

    ax.set_title("R1 and R2 Error Across All Graph Families")
    ax.set_xlabel("Edge failure probability q")
    ax.set_ylabel("Mean absolute error")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_subway_error(rows, output_path):
    """Compare R1, R2, and Rs on the subway-like graph only."""
    selected_rows = sorted(
        (
            row
            for row in rows
            if row["graph_name"] == "subway_like_small"
        ),
        key=lambda row: row["failure_probability"],
    )

    if not selected_rows:
        raise ValueError("No subway-like benchmark results were found.")

    if any(row["rs_estimate"] is None for row in selected_rows):
        raise ValueError(
            "Rs must be applicable to every subway-like test case."
        )

    q_values = [
        row["failure_probability"] for row in selected_rows
    ]

    fig, ax = plt.subplots(figsize=(9, 5))

    for method in ("r1", "r2", "rs"):
        ax.plot(
            q_values,
            [row[f"{method}_absolute_error"] for row in selected_rows],
            marker="o",
            label=f"{method.upper()} absolute error",
        )

    ax.set_title("Approximation Error on Subway-like Topology")
    ax.set_xlabel("Edge failure probability q")
    ax.set_ylabel("Absolute error")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def print_summary(rows):
    """Print runtime and error summaries."""
    print("\n=== Benchmark summary ===")
    print(f"Number of benchmark cases: {len(rows)}")

    for method in ("exact", "r1", "r2"):
        runtime_key = f"{method}_runtime_ms"
        median_runtime = median(
            row[runtime_key] for row in rows
        )

        print(
            f"{method}: median runtime = "
            f"{median_runtime:.4f} ms"
        )

    for method in ("r1", "r2"):
        error_key = f"{method}_absolute_error"
        average_error = mean(
            row[error_key] for row in rows
        )

        print(
            f"{method}: mean absolute error = "
            f"{average_error:.6f}"
        )

    rs_rows = [
        row
        for row in rows
        if row["rs_estimate"] is not None
    ]

    print(
        f"Rs: applicable cases = {len(rs_rows)} "
        f"out of {len(rows)}"
    )

    if rs_rows:
        print(
            "Rs: median runtime = "
            f"{median(row['rs_runtime_ms'] for row in rs_rows):.4f} ms"
        )

        print(
            "Rs: mean absolute error on applicable cases = "
            f"{mean(row['rs_absolute_error'] for row in rs_rows):.6f}"
        )


def main():
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = run_benchmark(repeats=3)

    save_results_csv(
        rows,
        output_dir / "reliability_benchmark.csv",
    )

    plot_reliability_curves(
        rows,
        output_dir / "reliability_curves.png",
    )

    plot_average_absolute_error(
        rows,
        output_dir / "approximation_error_summary.png",
    )

    plot_subway_error(
        rows,
        output_dir / "subway_approximation_error.png",
    )

    print_summary(rows)

    print("\nResults saved to:", output_dir.resolve())


if __name__ == "__main__":
    main()
