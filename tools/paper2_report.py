"""Validate the full evidence matrix before publishing any paper-level results."""

import csv
import json
import math
import random
import statistics as st
from collections import defaultdict

import bench
from paper2_evidence import (
    CONTROL,
    OUT,
    SEEDS,
    SETS,
    STANDARD,
    V2,
    V3,
    digest,
    validated,
)


def load_cohort(protocol, name):
    entries = {e["instance_id"]: e for e in bench.manifest(name)["entries"]}
    selected = set(protocol["cohorts"][name]["controls"])
    rows = defaultdict(dict)
    for job in protocol["jobs"]:
        if job["set"] != name:
            continue
        path = OUT / f"rows-{name}-{job['shard']}.csv"
        expected_ids = set(job["ids"])
        with path.open(newline="") as fp:
            for row in csv.DictReader(fp):
                i, n = row["instance_id"], row["algo"]
                if (
                    i not in expected_ids
                    or n in rows[i]
                    or row["set"] != name
                    or n not in protocol["sources"]
                    or row["source_sha256"] != protocol["sources"][n]
                    or not validated(row)
                    or row["case_study"] != str(i in selected)
                ):
                    raise ValueError(f"duplicate, stale or invalid row: {path} {i} {n}")
                rows[i][n] = row
    if set(rows) != set(entries):
        raise ValueError(f"incomplete instance coverage: {name}")
    for i, rs in rows.items():
        expected = set(STANDARD) | (set(CONTROL) if i in selected else set())
        if set(rs) != expected or len({r["deadline_us"] for r in rs.values()}) != 1:
            raise ValueError(f"invalid paired matrix: {name} {i}")
        if feasible(rs[V2]) and (not feasible(rs[V3]) or cost(rs[V3]) > cost(rs[V2])):
            raise ValueError(f"conditional dominance violated: {name} {i}")
        if i in selected:
            r = rs["equal-time-v2"]
            if (
                r["budget_time_ns"] != rs[V3]["runtime_ns"]
                or r["available_by_cutoff"] not in ("True", "False")
                or any(rs[n]["origin"] != "fresh" for n in (V2, V3, *CONTROL))
                or len({rs[n]["cpu"] for n in (V2, V3, *CONTROL)}) != 1
            ):
                raise ValueError(f"mismatched paired runtime protocol: {i}")
    return entries, rows


def feasible(row):
    return (
        row["deadline_met"] == "True" and row.get("available_by_cutoff", "") != "False"
    )


def cost(row):
    return int(row["compute_cost_ncu"])


def comparator(rs, n):
    if n.startswith("ProLiS "):
        costs = [cost(rs[k]) for k in SEEDS if feasible(rs[k])]
        if not costs:
            return None
        return min(costs) if n == "ProLiS best" else st.mean(costs)
    return cost(rs[n]) if feasible(rs[n]) else None


def percent(xs, q):
    if not xs:
        return None
    ordered = sorted(xs)
    p = (len(ordered) - 1) * q
    low = math.floor(p)
    return ordered[low] + (p - low) * (ordered[math.ceil(p)] - ordered[low])


def fmt(x):
    return "—" if x is None else f"{x:.4f}"


def cluster_ci(by_dag):
    # Resample source DAGs; their infrastructure and deadline variants stay together.
    clusters = [(sum(vals), len(vals)) for vals in by_dag.values()]
    if len(clusters) < 2:
        return (None, None)
    rng = random.Random(71023)
    means = []
    for _ in range(1000):
        picked = rng.choices(clusters, k=len(clusters))
        means.append(sum(s for s, _ in picked) / sum(n for _, n in picked))
    return percent(means, 0.025), percent(means, 0.975)


def comparison(entries, rows, ids, n, ci=False):
    ratios, clustered = [], defaultdict(list)
    met_a = met_b = both = wins = ties = losses = 0
    for i in ids:
        r = rows[i]
        a, b = r[V3], comparator(r, n)
        met_a += feasible(a)
        met_b += b is not None
        if not feasible(a) or b is None:
            continue
        both += 1
        c = cost(a)
        wins += c < b
        losses += c > b
        ties += c == b
        if b > 0:
            ratios.append(c / b)
            clustered[entries[i]["source_sha256"]].append(c / b)
    lo, hi = cluster_ci(clustered) if ci else (None, None)
    return [
        len(ids),
        met_a,
        met_b,
        both,
        wins,
        ties,
        losses,
        len(ratios),
        fmt(st.mean(ratios) if ratios else None),
        fmt(percent(ratios, 0.5)),
        fmt(lo),
        fmt(hi),
    ]


def table(path, header, rows):
    with path.open("w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(header)
        w.writerows(rows)


def exact_table(entries, rows, dst):
    src = bench.ROOT / "results/exact/exact-cost-60.csv"
    cases = {i for i, e in entries.items() if e["target_task_count"] == 60}
    seen, out = set(), []
    for r in bench.read_store(src):
        i = r["instance_id"]
        if r["set"] != "expansion" or i not in cases:
            continue
        if (
            i in seen
            or r["verified"] != "True"
            or r["status"] not in ("FEASIBLE", "OPTIMAL")
        ):
            raise ValueError(f"invalid CP-SAT reference: {i}")
        seen.add(i)
        bound, incumbent = int(r["solver_bound_ncu"]), int(r["cost_ncu"])
        if (
            int(r["deadline_us"]) != int(rows[i][V3]["deadline_us"])
            or incumbent <= 0
            or bound > incumbent
        ):
            raise ValueError(f"inconsistent CP-SAT reference: {i}")
        for n in (V2, V3):
            a = rows[i][n]
            if feasible(a) and (
                (bound > 0 and cost(a) < bound)
                or (r["status"] == "OPTIMAL" and cost(a) < incumbent)
            ):
                raise ValueError(f"cost below certified reference: {i} {n}")
            out.append(
                [
                    i,
                    n,
                    r["status"],
                    incumbent,
                    bound,
                    a["deadline_met"],
                    cost(a),
                    cost(a) / incumbent if feasible(a) else "",
                    cost(a) / bound if feasible(a) and bound > 0 else "",
                ]
            )
    if seen != cases:
        raise ValueError("incomplete CP-SAT reference coverage")
    table(
        dst / "cp-sat.csv",
        [
            "instance",
            "algorithm",
            "solver_status",
            "incumbent",
            "lower_bound",
            "deadline_met",
            "cost",
            "ratio_to_incumbent",
            "ratio_to_bound",
        ],
        out,
    )
    return out


def historical_sample(entries, rows, dest):
    reference = bench.ROOT / "results/paper2/dcr-cost-v3-expansion-sample-compact.csv"
    ordered = sorted(entries)
    paired = []
    for old in bench.read_store(reference):
        i = ordered[int(old["index"])]
        current = rows[i][V3]
        ok = (
            current["makespan_us"] == old["v3_makespan_us"]
            and current["compute_cost_ncu"] == old["v3_compute_cost_ncu"]
        )
        paired.append(
            [
                i,
                old["v3_makespan_us"],
                current["makespan_us"],
                old["v3_compute_cost_ncu"],
                current["compute_cost_ncu"],
                ok,
            ]
        )
    table(
        dest / "sample-replay.csv",
        [
            "instance",
            "historical_makespan",
            "fresh_makespan",
            "historical_cost",
            "fresh_cost",
            "matched",
        ],
        paired,
    )
    if (
        len({r[0] for r in paired}) != 495
        or len(paired) != 495
        or not all(r[-1] for r in paired)
    ):
        raise ValueError("historical 495-case v3 cost/makespan replay mismatch")


def report(p):
    dest = OUT / "bundle"
    dest.mkdir(exist_ok=True)
    header = [
        "set",
        "group",
        "versus",
        "instances",
        "v3_met",
        "other_met",
        "both_met",
        "wins",
        "ties",
        "losses",
        "positive_denominator_pairs",
        "mean_ratio",
        "median_ratio",
        "cluster_ci_low",
        "cluster_ci_high",
    ]
    comparisons, runtimes, coverage, all_rows, cp = [], [], [], [], []
    summary = [
        "# DCR-Cost evidence",
        "",
        f"Execution commit `{p['execution_commit']}`.",
        "Cost comparisons use instances where both methods meet the deadline. Ratios are v3 / comparator.",
        "ProLiS mean and best use feasible seeds only. A per-seed breakdown is in coverage.csv.",
        "Intervals resample source workflows. Runtime ratios use fresh runs on the same worker.",
        "The equal-time control counts only incumbents available at the v3 wall-time cutoff.",
        "",
    ]
    for name in SETS:
        cohort = p["cohorts"][name]
        if (
            digest(bench.ROOT / "manifests" / bench.SET_MANIFESTS[name])
            != cohort["manifest_sha256"]
        ):
            raise ValueError(f"manifest changed: {name}")
        entries, rows = load_cohort(p, name)
        selected = cohort["controls"]
        all_rows.extend(r for rs in rows.values() for r in rs.values())
        groups = defaultdict(list)
        for i, e in entries.items():
            for key in (
                "family",
                "qos_profile",
                "target_task_count",
                "source_kind",
                "scenario_profile",
                "resource_scale",
            ):
                if key in e:
                    groups[f"{key}={e[key]}"].append(i)
        summary += [
            f"## {name.title()}",
            "",
            "| Comparator | Both meet deadline | v3 cheaper / equal / costlier | Mean cost ratio | 95% interval |",
            "|---|---:|---:|---:|---:|",
        ]
        for n in (
            "dcr-cost-v1",
            V2,
            "icpcp",
            "cmas",
            "ProLiS mean",
            "ProLiS best",
            *CONTROL,
        ):
            ids = selected if n in CONTROL else list(entries)
            result = comparison(entries, rows, ids, n, True)
            comparisons.append(
                [name, "paired sample" if n in CONTROL else "all", n, *result]
            )
            summary.append(
                f"| {n} | {result[3]}/{len(ids)} | {result[4]} / {result[5]} / {result[6]} | "
                f"{result[8]} | {result[10]} – {result[11]} |"
            )
            if n not in CONTROL:
                for group, subset in sorted(groups.items()):
                    comparisons.append(
                        [name, group, n, *comparison(entries, rows, subset, n)]
                    )
        for n in (*STANDARD, *CONTROL):
            rr = [rs[n] for rs in rows.values() if n in rs]
            coverage.append(
                [
                    name,
                    n,
                    len(rr),
                    sum(feasible(r) for r in rr),
                    sum(r["origin"] == "stored" for r in rr),
                    sum(r["available_by_cutoff"] == "False" for r in rr),
                ]
            )
        for size in sorted({entries[i]["target_task_count"] for i in selected}):
            sample = [
                rows[i] for i in selected if entries[i]["target_task_count"] == size
            ]
            a = [int(rs[V2]["runtime_ns"]) / 1e9 for rs in sample]
            b = [int(rs[V3]["runtime_ns"]) / 1e9 for rs in sample]
            runtimes.append(
                [
                    name,
                    size,
                    len(sample),
                    st.median(a),
                    st.median(b),
                    st.median(y / x for x, y in zip(a, b)),
                    percent(b, 0.9),
                    max(b),
                ]
            )
        if name == "expansion":
            if (
                digest(bench.ROOT / "results/exact/exact-cost-60.csv")
                != p["exact_csv_sha256"]
            ):
                raise ValueError("exact reference changed")
            cp = exact_table(entries, rows, dest)
            historical_sample(entries, rows, dest)
        summary += [""]
    summary += [
        "## CP-SAT comparisons on 60-task expansion instances",
        "",
        "| Algorithm | Reference | Feasible pairs | Median ratio | p90 | Maximum |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for n in (V2, V3):
        for ref in ("all verified incumbents", "proven optimal"):
            rr = [
                r[7]
                for r in cp
                if r[1] == n
                and r[7] != ""
                and (ref == "all verified incumbents" or r[2] == "OPTIMAL")
            ]
            summary.append(
                f"| {n} | {ref} | {len(rr)} | {fmt(percent(rr, 0.5))} | {fmt(percent(rr, 0.9))} | {fmt(max(rr) if rr else None)} |"
            )
    from paper2_evidence import FIELDS

    table(dest / "runs.csv", FIELDS, ([r[k] for k in FIELDS] for r in all_rows))
    table(dest / "comparisons.csv", header, comparisons)
    table(
        dest / "coverage.csv",
        [
            "set",
            "algorithm",
            "valid",
            "met_deadline_by_cutoff",
            "reused",
            "unavailable_by_cutoff",
        ],
        coverage,
    )
    table(
        dest / "runtime.csv",
        [
            "set",
            "tasks",
            "cases",
            "median_v2_s",
            "median_v3_s",
            "median_paired_ratio",
            "v3_p90_s",
            "v3_max_s",
        ],
        runtimes,
    )
    (dest / "protocol.json").write_bytes((OUT / "protocol.json").read_bytes())
    (dest / "summary.md").write_text("\n".join(summary) + "\n")
    hashes = {
        f.name: digest(f) for f in sorted(dest.iterdir()) if f.name != "sha256.json"
    }
    (dest / "sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
