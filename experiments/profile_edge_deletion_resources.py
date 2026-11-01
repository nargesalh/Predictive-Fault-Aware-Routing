"""Resource profile of the Edge Deletion estimator (separate from the 5 algorithms).

Edge Deletion estimates the AVERAGE reliability (integral over q), not R(q) for one
failure probability, so it is profiled on its own and never joined with the
accuracy dataset of R(q). Baseline: exact average reliability.
"""
import argparse
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.profile_algorithm_resources import graph_signature, iqr, write_csv, environment_info

FIELDS = [
    "graph_name", "num_nodes", "num_edges", "algorithm", "trials", "seed",
    "estimate", "runtime_median_ms", "runtime_iqr_ms",
    "peak_python_memory_median_mb", "status", "reason",
    "python_version", "platform", "timing_repeats", "memory_repeats",
]
DEFAULT_TRIALS = (100, 500, 1000, 2500)


def measure(func, graph, timing_repeats, memory_repeats):
    func(graph)  # warm-up
    times, value = [], None
    for _ in range(timing_repeats):
        start = time.perf_counter()
        value = func(graph)
        times.append((time.perf_counter() - start) * 1000.0)
    mems = []
    for _ in range(memory_repeats):
        tracemalloc.start()
        try:
            func(graph)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        mems.append(peak / (1024.0 * 1024.0))
    return value, statistics.median(times), iqr(times), statistics.median(mems)


def profile_edge_deletion(graphs, trial_counts=DEFAULT_TRIALS, seed=42,
                          timing_repeats=5, memory_repeats=3):
    if timing_repeats < 5:
        raise ValueError("timing_repeats must be at least 5.")
    if memory_repeats < 1:
        raise ValueError("memory_repeats must be at least 1.")
    from reliability import (
        all_terminal_average_reliability_exact,
        estimate_average_reliability,
    )

    rows = []
    for name, graph in graphs.items():
        before = graph_signature(graph)
        jobs = [("exact_average", None, lambda g: all_terminal_average_reliability_exact(g))]
        for trials in trial_counts:
            jobs.append(("edge_deletion", trials,
                         lambda g, t=trials: estimate_average_reliability(g, trials=t, seed=seed)))
        for algorithm, trials, func in jobs:
            row = {f: "" for f in FIELDS}
            row.update(graph_name=name, num_nodes=graph.number_of_nodes(),
                       num_edges=graph.number_of_edges(), algorithm=algorithm,
                       trials=trials if trials else "", seed=seed if trials else "")
            row.update(environment_info())
            try:
                value, med, spread, mem = measure(func, graph, timing_repeats, memory_repeats)
            except Exception as exc:
                row["status"] = "failed"
                row["reason"] = type(exc).__name__ + ": " + str(exc)
                rows.append(row)
                continue
            if graph_signature(graph) != before:
                row["status"], row["reason"] = "failed", "graph_modified"
            else:
                row.update(estimate=value, runtime_median_ms=med, runtime_iqr_ms=spread,
                           peak_python_memory_median_mb=mem, status="ok",
                           timing_repeats=timing_repeats, memory_repeats=memory_repeats)
            rows.append(row)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", nargs="+", type=int, default=list(DEFAULT_TRIALS))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timing-repeats", type=int, default=5)
    parser.add_argument("--memory-repeats", type=int, default=3)
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args(argv)
    from experiments.compare_edge_deletion import build_edge_deletion_graphs
    rows = profile_edge_deletion(build_edge_deletion_graphs(), args.trials, args.seed,
                                 args.timing_repeats, args.memory_repeats)
    out = Path(args.output_dir) / "edge_deletion_resource_profile.csv"
    write_csv(out, FIELDS, rows)
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("rows:", len(rows), "| status counts:", counts)
    print("saved to:", out.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
