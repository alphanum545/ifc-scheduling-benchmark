"""Join PACM and DCDS to the archived v3 runs, checking frozen evidence first."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import lzma
import statistics as st
import zipfile
from collections import defaultdict
from pathlib import Path

import bench
from paper2_evidence import validated
from paper2_report import cluster_ci

SEEDS = [f"pacm-s{i}" for i in range(10)]


def write_rows(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def archived_v3(archive, cohort):
    with zipfile.ZipFile(archive) as bundle:
        protocol = json.loads(bundle.read("protocol.json"))
        manifest = bench.ROOT / "manifests" / bench.SET_MANIFESTS[cohort]
        if hashlib.sha256(manifest.read_bytes()).hexdigest() != protocol["cohorts"][cohort]["manifest_sha256"]:
            raise ValueError("cohort fingerprint differs")
        content = bundle.read("runs.csv")
        if hashlib.sha256(content).hexdigest() != json.loads(bundle.read("sha256.json"))["runs.csv"]:
            raise ValueError("archive digest differs")
        rows = csv.DictReader(io.StringIO(content.decode()))
        return {r["instance_id"]: r for r in rows if r["algo"] == "dcr-cost-v3" and r["set"] == cohort}


def summarize(ids, data, entries, name, overall):
    wins = ties = losses = paired = covered = 0
    clusters = defaultdict(list)
    runtimes = []
    for i in ids:
        v3, raw = data[i]
        rows = [raw["dcds"]] if name == "DCDS" else [raw[k] for k in SEEDS]
        runtimes.extend(int(r["runtime_ns"]) / 1e9 for r in rows)
        feasible = [int(r["compute_cost_ncu"]) for r in rows if r["deadline_met"] == "True"]
        if not feasible:
            continue
        covered += 1
        if v3["deadline_met"] != "True":
            continue
        paired += 1
        cost = st.mean(feasible) if name == "PACM mean" else min(feasible)
        baseline = int(v3["compute_cost_ncu"])
        wins += baseline < cost
        ties += baseline == cost
        losses += baseline > cost
        if cost:
            clusters[entries[i]["source_sha256"]].append(baseline / cost)
    ratios = [v for group in clusters.values() for v in group]
    lo, hi = cluster_ci(clusters) if overall else (None, None)
    return dict(method=name, cases=len(ids), covered=covered, paired=paired, wins=wins,
                ties=ties, losses=losses, positive_cost_pairs=len(ratios),
                mean_ratio=st.mean(ratios) if ratios else None,
                median_ratio=st.median(ratios) if ratios else None, ci_low=lo, ci_high=hi,
                median_policy_seconds_per_attempt=st.median(runtimes))


def report(args):
    cohort = args.cohort
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    entries = {e["instance_id"]: e for e in bench.manifest(cohort)["entries"]}
    v3 = archived_v3(args.archive, cohort)
    raw = defaultdict(dict)
    registry = bench.registry()
    with gzip.open(args.dcds, "rt") as dr, args.pacm.open() as pr:
        for stream, names in [(dr, ["dcds"]), (pr, SEEDS)]:
            for r in csv.DictReader(stream):
                i, k = r["instance_id"], r["algo"]
                if (i not in entries or k not in names or k in raw[i] or not validated(r)
                        or r["source_sha256"] != registry[k]["source_sha256"]
                        or r["deadline_us"] != v3[i]["deadline_us"]):
                    raise ValueError(f"invalid comparator row {i}, {k}")
                raw[i][k] = r
    if set(entries) != set(raw) or set(entries) != set(v3):
        raise ValueError("incomplete instance coverage")
    if any(set(r) != set(["dcds", *SEEDS]) for r in raw.values()):
        raise ValueError("incomplete seed coverage")
    data = {i: (v3[i], raw[i]) for i in entries}
    groups = defaultdict(list)
    for i, e in sorted(entries.items()):
        groups["all", "all"].append(i)
        for k in ["family", "qos_profile", "resource_scale", "target_task_count", "scenario_profile"]:
            groups[k, e[k]].append(i)
    summary = []
    for (dimension, value), ids in groups.items():
        for name in ("PACM best", "PACM mean", "DCDS"):
            summary.append(dict(group=dimension, value=value, **summarize(ids, data, entries, name, dimension == "all")))
    write_rows(out / "comparisons.csv", summary)
    write_rows(out / "seed_coverage.csv", [dict(seed=k, cases=len(entries),
               met=sum(raw[i][k]["deadline_met"] == "True" for i in entries)) for k in SEEDS])
    if cohort == "expansion":
        exact = []
        with (bench.ROOT / "results/exact/exact-cost-60.csv").open() as stream:
            for ref in csv.DictReader(stream):
                if ref["set"] != cohort:
                    continue
                i = ref["instance_id"]
                assert ref["verified"] == "True" and ref["deadline_us"] == v3[i]["deadline_us"]
                for k in ["dcds", *SEEDS]:
                    r = raw[i][k]
                    c = int(r["compute_cost_ncu"])
                    met = r["deadline_met"] == "True"
                    upper, lower = int(ref["cost_ncu"]), int(ref["solver_bound_ncu"])
                    assert not met or c >= lower and (ref["status"] != "OPTIMAL" or c >= upper)
                    exact.append(dict(instance_id=i, method=k, met=met, cost=c, status=ref["status"],
                                      incumbent=upper, lower_bound=lower, ratio_to_incumbent=c/upper if met else None))
        assert len(exact) == 270 * (len(SEEDS) + 1)
        write_rows(out / "exact.csv", exact)
    # Separate raw files by seed pair, keeping each one straightforward to download.
    for a, b in zip(SEEDS[::2], SEEDS[1::2]):
        with lzma.open(out / f"{a}_{b}.csv.xz", "wt", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=bench.FIELDS)
            writer.writeheader()
            for i in sorted(raw):
                writer.writerows([raw[i][a], raw[i][b]])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", choices=("expansion","unseen"), required=True)
    for arg in ("archive", "dcds", "pacm", "out"):
        parser.add_argument("--" + arg, type=Path, required=True)
    report(parser.parse_args())
