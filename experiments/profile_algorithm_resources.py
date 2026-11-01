import argparse
import csv
import importlib
import platform
import random
import statistics
import sys
import time
import tracemalloc
from collections import namedtuple
from pathlib import Path

import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

Algorithm = namedtuple("Algorithm", ["name", "func", "uses_mc", "applicable"])

SUMMARY_FIELDS = [
    "graph_name",
    "num_nodes",
    "num_edges",
    "failure_probability",
    "algorithm",
    "mc_trials",
    "mc_seed",
    "runtime_median_ms",
    "runtime_iqr_ms",
    "peak_python_memory_median_mb",
    "status",
    "reason",
    "python_version",
    "platform",
    "timing_repeats",
    "memory_repeats",
]

RAW_FIELDS = [
    "graph_name",
    "failure_probability",
    "algorithm",
    "measurement",
    "repeat",
    "value",
    "unit",
    "result_value",
]

DEFAULT_PROBABILITIES = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
DEFAULT_ALGORITHMS = ["exact", "r1", "r2", "rs", "mc"]
EXACT_MAX_EDGES = 16

PROJECT_PACKAGE = "reliability"
PROJECT_FUNCTIONS = {
    "exact": "all_terminal_reliability_exact",
    "r1": "first_order_approximation",
    "r2": "second_order_approximation",
    "rs": "subway_type_approximation",
    "mc": "estimate_all_terminal_reliability_monte_carlo",
}
NOT_APPLICABLE_ERROR_NAMES = ("SubwayApproximationNotApplicable",)
TOPOLOGY_MODULE = "experiments.compare_approximations"
TOPOLOGY_BUILDER = "build_benchmark_graphs"
PROBABILITY_NAMES = ("DEFAULT_Q_VALUES", "FAILURE_PROBABILITIES", "PROBABILITIES", "FAILURE_PROBS")


class ImplementationUnavailable(Exception):
    pass


class NotApplicableError(Exception):
    pass


def validate_probability(p):
    if isinstance(p, bool) or not isinstance(p, (int, float)):
        raise ValueError("failure probability must be a number.")
    if not 0.0 < p < 1.0:
        raise ValueError("failure probability must be strictly between 0 and 1.")


def validate_config(config):
    if config["timing_repeats"] < 5:
        raise ValueError("timing_repeats must be at least 5.")
    if config["memory_repeats"] < 1:
        raise ValueError("memory_repeats must be at least 1.")
    if config["mc_trials"] < 1:
        raise ValueError("mc_trials must be a positive integer.")


def is_connected_state(nodes, edges):
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    components = len(parent)
    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            components -= 1
    return components == 1


def reference_exact(graph, p):
    nodes = list(graph.nodes())
    edges = list(graph.edges())
    m = len(edges)
    total = 0.0
    for mask in range(1 << m):
        up = [edges[i] for i in range(m) if (mask >> i) & 1]
        if is_connected_state(nodes, up):
            k = len(up)
            total += ((1.0 - p) ** k) * (p ** (m - k))
    return total


def reference_monte_carlo(graph, p, trials, seed):
    rng = random.Random(seed)
    nodes = list(graph.nodes())
    edges = list(graph.edges())
    successes = 0
    for _ in range(trials):
        up = [e for e in edges if rng.random() >= p]
        if is_connected_state(nodes, up):
            successes += 1
    return successes / trials


def always_applicable(graph):
    return True, ""


def limit_edges(limit):
    def check(graph):
        if graph.number_of_edges() > limit:
            return False, "too_many_edges_for_exact"
        return True, ""

    return check


def no_bridges(graph):
    if graph.number_of_edges() == 0:
        return False, "graph_has_no_edges"
    if next(nx.bridges(graph), None) is not None:
        return False, "graph_has_bridges"
    return True, ""


def load_project_function(key):
    try:
        module = importlib.import_module(PROJECT_PACKAGE)
    except ImportError:
        return None
    func = getattr(module, PROJECT_FUNCTIONS[key], None)
    if callable(func):
        return func
    return None


def project_runner(key, uses_mc):
    func = load_project_function(key)
    name = PROJECT_PACKAGE + "." + PROJECT_FUNCTIONS[key]

    def run(graph, p, trials=None, seed=None):
        if func is None:
            raise ImplementationUnavailable("function not found: " + name)
        try:
            if uses_mc:
                return func(graph, p, trials=trials, seed=seed)
            return func(graph, p)
        except Exception as exc:
            if type(exc).__name__ in NOT_APPLICABLE_ERROR_NAMES:
                raise NotApplicableError(type(exc).__name__ + ": " + str(exc)) from exc
            raise

    return run


def project_registry(exact_max_edges=EXACT_MAX_EDGES):
    return {
        "exact": Algorithm("exact", project_runner("exact", False), False, limit_edges(exact_max_edges)),
        "r1": Algorithm("r1", project_runner("r1", False), False, always_applicable),
        "r2": Algorithm("r2", project_runner("r2", False), False, always_applicable),
        "rs": Algorithm("rs", project_runner("rs", False), False, always_applicable),
        "mc": Algorithm("mc", project_runner("mc", True), True, always_applicable),
    }


def reference_registry(exact_max_edges=EXACT_MAX_EDGES):
    def mc(graph, p, trials=None, seed=None):
        return reference_monte_carlo(graph, p, trials, seed)

    return {
        "exact": Algorithm("exact", reference_exact, False, limit_edges(exact_max_edges)),
        "mc": Algorithm("mc", mc, True, always_applicable),
    }


def default_topologies():
    return {
        "path_8": nx.path_graph(8),
        "cycle_8": nx.cycle_graph(8),
        "complete_5": nx.complete_graph(5),
        "regular_3_8": nx.random_regular_graph(3, 8, seed=1),
        "ladder_5": nx.ladder_graph(5),
        "wheel_7": nx.wheel_graph(7),
        "barbell_4_0": nx.barbell_graph(4, 0),
        "mesh_3x3": nx.convert_node_labels_to_integers(nx.grid_2d_graph(3, 3)),
    }


def project_topologies():
    module = importlib.import_module(TOPOLOGY_MODULE)
    built = getattr(module, TOPOLOGY_BUILDER)()
    if isinstance(built, dict):
        return dict(built)
    graphs = {}
    for item in built:
        if isinstance(item, tuple) and len(item) == 2:
            graphs[item[0]] = item[1]
        else:
            raise ValueError("unsupported format returned by " + TOPOLOGY_BUILDER)
    return graphs


def project_probabilities():
    try:
        module = importlib.import_module(TOPOLOGY_MODULE)
    except ImportError:
        return None
    for name in PROBABILITY_NAMES:
        values = getattr(module, name, None)
        if values:
            return [float(v) for v in values]
    return None


def graph_signature(graph):
    nodes = tuple(sorted(str(n) for n in graph.nodes()))
    edges = tuple(
        sorted(
            (tuple(sorted((str(u), str(v)))), repr(sorted(d.items())))
            for u, v, d in graph.edges(data=True)
        )
    )
    return nodes, edges


def call_algorithm(algo, graph, p, config):
    if algo.uses_mc:
        return algo.func(graph, p, trials=config["mc_trials"], seed=config["mc_seed"])
    return algo.func(graph, p)


def time_once(algo, graph, p, config):
    start = time.perf_counter()
    value = call_algorithm(algo, graph, p, config)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, value


def memory_once(algo, graph, p, config):
    tracemalloc.start()
    try:
        value = call_algorithm(algo, graph, p, config)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak / (1024.0 * 1024.0), value


def iqr(values):
    q = statistics.quantiles(values, n=4, method="inclusive")
    return q[2] - q[0]


def environment_info():
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


def profile_combination(graph_name, graph, p, algo, config):
    validate_probability(p)
    validate_config(config)
    summary = {field: "" for field in SUMMARY_FIELDS}
    summary.update(
        {
            "graph_name": graph_name,
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges(),
            "failure_probability": p,
            "algorithm": algo.name,
        }
    )
    summary.update(environment_info())
    if algo.uses_mc:
        summary["mc_trials"] = config["mc_trials"]
        summary["mc_seed"] = config["mc_seed"]

    applicable, reason = algo.applicable(graph)
    if not applicable:
        summary["status"] = "not_applicable"
        summary["reason"] = reason
        return summary, []

    before = graph_signature(graph)
    raw = []

    def raw_row(kind, index, value, unit, result):
        return {
            "graph_name": graph_name,
            "failure_probability": p,
            "algorithm": algo.name,
            "measurement": kind,
            "repeat": index,
            "value": value,
            "unit": unit,
            "result_value": result,
        }

    try:
        call_algorithm(algo, graph, p, config)
        times = []
        for i in range(config["timing_repeats"]):
            ms, value = time_once(algo, graph, p, config)
            times.append(ms)
            raw.append(raw_row("time", i, ms, "ms", value))
        mems = []
        for i in range(config["memory_repeats"]):
            mb, value = memory_once(algo, graph, p, config)
            mems.append(mb)
            raw.append(raw_row("memory", i, mb, "MB", value))
    except NotApplicableError as exc:
        summary["status"] = "not_applicable"
        summary["reason"] = str(exc)
        return summary, []
    except ImplementationUnavailable as exc:
        summary["status"] = "unavailable"
        summary["reason"] = str(exc)
        return summary, []
    except Exception as exc:
        summary["status"] = "failed"
        summary["reason"] = type(exc).__name__ + ": " + str(exc)
        return summary, []

    if graph_signature(graph) != before:
        summary["status"] = "failed"
        summary["reason"] = "graph_modified"
        return summary, []

    summary["runtime_median_ms"] = statistics.median(times)
    summary["runtime_iqr_ms"] = iqr(times)
    summary["peak_python_memory_median_mb"] = statistics.median(mems)
    summary["status"] = "ok"
    summary["timing_repeats"] = config["timing_repeats"]
    summary["memory_repeats"] = config["memory_repeats"]
    return summary, raw


def run_profiling(graphs, probabilities, algorithm_names, registry, config):
    validate_config(config)
    for name in algorithm_names:
        if name not in registry:
            raise ValueError("unknown algorithm: " + str(name))
    for p in probabilities:
        validate_probability(p)
    summary_rows = []
    raw_rows = []
    for graph_name, graph in graphs.items():
        for p in probabilities:
            for name in algorithm_names:
                summary, raw = profile_combination(graph_name, graph, p, registry[name], config)
                summary_rows.append(summary)
                raw_rows.extend(raw)
    return summary_rows, raw_rows


def write_csv(path, fields, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Profile time and Python memory of reliability algorithms.")
    parser.add_argument("--source", choices=["project", "reference"], default="project")
    parser.add_argument("--algorithms", nargs="+", default=DEFAULT_ALGORITHMS)
    parser.add_argument("--graphs", nargs="+", default=None)
    parser.add_argument("--probabilities", nargs="+", type=float, default=None)
    parser.add_argument("--topologies", choices=["auto", "project", "builtin"], default="auto")
    parser.add_argument("--timing-repeats", type=int, default=5)
    parser.add_argument("--memory-repeats", type=int, default=3)
    parser.add_argument("--mc-trials", type=int, default=1000)
    parser.add_argument("--mc-seed", type=int, default=42)
    parser.add_argument("--exact-max-edges", type=int, default=EXACT_MAX_EDGES)
    parser.add_argument("--output-dir", default="outputs")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config = {
        "timing_repeats": args.timing_repeats,
        "memory_repeats": args.memory_repeats,
        "mc_trials": args.mc_trials,
        "mc_seed": args.mc_seed,
    }
    if args.source == "project":
        registry = project_registry(args.exact_max_edges)
    else:
        registry = reference_registry(args.exact_max_edges)
    use_project = args.topologies == "project" or (args.topologies == "auto" and args.source == "project")
    graphs = None
    probabilities = args.probabilities
    if use_project:
        try:
            graphs = project_topologies()
            print("topologies: project benchmark (" + str(len(graphs)) + " graphs)")
            if probabilities is None:
                probabilities = project_probabilities()
        except (ImportError, AttributeError) as exc:
            if args.topologies == "project":
                raise
            print("project topologies unavailable, using builtin:", exc)
    if graphs is None:
        graphs = default_topologies()
        print("topologies: builtin sample (" + str(len(graphs)) + " graphs)")
    if probabilities is None:
        probabilities = DEFAULT_PROBABILITIES
    print("probabilities:", probabilities)
    if args.graphs is not None:
        missing = [g for g in args.graphs if g not in graphs]
        if missing:
            raise ValueError("unknown graphs: " + ", ".join(missing))
        graphs = {g: graphs[g] for g in args.graphs}
    algorithm_names = [a for a in args.algorithms if a in registry or args.source == "project"]
    summary_rows, raw_rows = run_profiling(graphs, probabilities, algorithm_names, registry, config)
    out = Path(args.output_dir)
    write_csv(out / "resource_profile_raw.csv", RAW_FIELDS, raw_rows)
    write_csv(out / "resource_profile_summary.csv", SUMMARY_FIELDS, summary_rows)
    counts = {}
    for row in summary_rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print("summary rows:", len(summary_rows), "raw rows:", len(raw_rows))
    print("status counts:", counts)
    print("saved to:", out.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
