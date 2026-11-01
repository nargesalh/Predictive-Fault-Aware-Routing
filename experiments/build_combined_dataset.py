"""Join the accuracy dataset (AI side) with the resource profile (hardware side).

Join key: graph_name + failure_probability + algorithm.
Output: one row per key with error, time and memory side by side.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

KEY = ("graph_name", "failure_probability", "algorithm")
RESOURCE_COLUMNS = [
    "runtime_median_ms",
    "runtime_iqr_ms",
    "peak_python_memory_median_mb",
    "resource_status",
    "resource_reason",
    "mc_trials",
    "mc_seed",
    "timing_repeats",
    "memory_repeats",
    "python_version",
    "platform",
]
FIRST_COLUMNS = ["experiment_id", "topology_type"]


def topology_type(graph_name):
    """path_5 -> path, random_3_regular_6 -> random_regular, grid_3x3 -> grid."""
    parts = [p for p in graph_name.split("_") if not re.fullmatch(r"[0-9x]+", p)]
    return "_".join(parts) if parts else graph_name


def make_key(row):
    return (
        row["graph_name"],
        round(float(row["failure_probability"]), 9),
        row["algorithm"],
    )


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def combine(accuracy_rows, resource_rows):
    if not accuracy_rows or not resource_rows:
        raise ValueError("Both input files must contain rows.")
    accuracy = {}
    for row in accuracy_rows:
        key = make_key(row)
        if key in accuracy:
            raise ValueError("Duplicate key in accuracy dataset: " + str(key))
        accuracy[key] = row
    resources = {}
    for row in resource_rows:
        key = make_key(row)
        if key in resources:
            raise ValueError("Duplicate key in resource profile: " + str(key))
        resources[key] = row
    if set(accuracy) != set(resources):
        only_a = len(set(accuracy) - set(resources))
        only_r = len(set(resources) - set(accuracy))
        raise ValueError(
            "Keys differ: %d only in accuracy, %d only in resources." % (only_a, only_r)
        )

    combined = []
    for index, key in enumerate(sorted(accuracy), start=1):
        acc, res = accuracy[key], resources[key]
        applicable = str(acc["is_applicable"]).strip().lower() == "true"
        if applicable != (res["status"] == "ok"):
            raise ValueError("Applicability mismatch for key " + str(key))
        row = {
            "experiment_id": "exp_%04d" % index,
            "topology_type": topology_type(acc["graph_name"]),
        }
        row.update(acc)
        row["resource_status"] = res["status"]
        row["resource_reason"] = res["reason"]
        for column in RESOURCE_COLUMNS:
            if column not in ("resource_status", "resource_reason"):
                row[column] = res[column]
        combined.append(row)
    return combined


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accuracy", default="data/benchmarks/selector_accuracy_dataset.csv")
    parser.add_argument("--resources", default="data/benchmarks/resource_profile_summary.csv")
    parser.add_argument("--output", default="data/benchmarks/selector_full_dataset.csv")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    for path in (args.accuracy, args.resources):
        if not Path(path).exists():
            raise FileNotFoundError("Input not found: " + path)
    rows = combine(read_csv(args.accuracy), read_csv(args.resources))
    write_csv(args.output, rows)
    ok = sum(1 for r in rows if r["resource_status"] == "ok")
    print("combined rows:", len(rows), "| with resources:", ok, "| not applicable:", len(rows) - ok)
    print("saved to:", Path(args.output).resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
