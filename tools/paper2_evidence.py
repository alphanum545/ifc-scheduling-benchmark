"""One frozen evidence protocol. Use plan, shard, then report. No shared result-store writes."""

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import bench

SETS = ("expansion", "unseen")
V2, V3 = "dcr-cost-v2", "dcr-cost-v3"
SEEDS = tuple(f"prolis-s{i}" for i in range(10))
STANDARD = ("dcr-cost-v1", V2, V3, "icpcp", "cmas", *SEEDS)
CONTROL = ("pricing-only", "polish-only", "equal-time-v2")
EXTRA = [
    "set",
    "origin",
    "case_study",
    "budget_time_ns",
    "available_by_cutoff",
    "extra_split_trials",
]
FIELDS = bench.FIELDS + EXTRA
OUT = Path("evidence")
FROZEN = "d4f8468b27f0f0f5b005f82f4ec3c7ea89590a34"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sources():
    registry = bench.registry()
    hashes = {n: registry[n]["source_sha256"] for n in STANDARD}
    fingerprint = bench.source_hash(
        registry[V3]["sources"] + ["tools/paper2_controls.py"]
    )
    hashes.update(dict.fromkeys(CONTROL, fingerprint))
    return hashes


def study_ids(entries):
    # One case per family × size × QoS. Selection uses only the identifier and
    # is fixed before any algorithm sees the unseen instances.
    groups = defaultdict(list)
    for e in entries:
        groups[e["family"], e["target_task_count"], e["qos_profile"]].append(
            e["instance_id"]
        )
    return {
        min(ids, key=lambda i: hashlib.sha256(i.encode()).digest())
        for ids in groups.values()
    }


def validated(r):
    try:
        return (
            r["status"] == "ok"
            and str(r["valid"]) == "True"
            and str(r["deterministic"]) != "False"
            and int(r["reps"]) >= 1
            and len(r["schedule_sha256"]) == 64
            and int(r["runtime_ns"]) > 0
            and int(r["compute_cost_ncu"]) >= 0
            and int(r["deadline_us"]) > 0
            and int(r["makespan_us"]) >= 0
            and str(r["deadline_met"])
            == str(int(r["makespan_us"]) <= int(r["deadline_us"]))
        )
    except (KeyError, ValueError, TypeError):
        return False


def stored(hashes):
    valid = {}
    for n in STANDARD:
        for row in bench.read_store(bench.STORE_DIR / f"{n}.csv"):
            if (
                row["algo"] == n
                and row["source_sha256"] == hashes[n]
                and validated(row)
            ):
                key = (row["instance_id"], n)
                if key in valid:
                    raise ValueError(f"duplicate stored row: {key}")
                valid[key] = row
    return valid


def case_matrix(entries, set_name, shards):
    # Weight by size; put the more expensive paired cases first at each size.
    selected = study_ids(entries)
    buckets = [[] for _ in range(shards)]
    load = [0.0] * shards

    def weight(e):
        return e["target_task_count"] ** 1.6 * (
            2 if e["instance_id"] in selected else 1
        )

    for e in sorted(entries, key=lambda e: (-weight(e), e["instance_id"])):
        slot = min(range(shards), key=load.__getitem__)
        buckets[slot].append(e["instance_id"])
        load[slot] += weight(e)
    return [
        {"set": set_name, "shard": i, "ids": ids}
        for i, ids in enumerate(buckets)
        if ids
    ]


def plan():
    import subprocess

    OUT.mkdir(exist_ok=True)
    # A later merge or dispatch cannot silently change the method, evaluator, or cohorts.
    frozen_paths = [
        "algorithms",
        "algorithms.toml",
        "requirements.txt",
        "tools/bench.py",
        "tools/data.py",
        "tools/exact_cost.py",
        "manifests/expansion-v1.json",
        "manifests/unseen-v1.json",
    ]
    subprocess.run(
        ["git", "diff", "--exit-code", FROZEN, "HEAD", "--", *frozen_paths], check=True
    )
    matrix, cohorts = [], {}
    for s in SETS:
        entries = bench.manifest(s)["entries"]
        ids = {e["instance_id"] for e in entries}
        if (
            len(entries) != len(ids)
            or len(ids) != {"expansion": 1890, "unseen": 2241}[s]
        ):
            raise ValueError(f"unexpected frozen manifest: {s}")
        cohorts[s] = {
            "cases": len(ids),
            "controls": sorted(study_ids(entries)),
            "manifest_sha256": digest(
                bench.ROOT / "manifests" / bench.SET_MANIFESTS[s]
            ),
        }
        matrix.extend(case_matrix(entries, s, 36 if s == "expansion" else 60))
    p = {
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_repository": os.environ.get("GITHUB_REPOSITORY"),
        "frozen_algorithm_commit": FROZEN,
        "execution_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "sources": sources(),
        "cohorts": cohorts,
        "jobs": matrix,
        "requirements": (bench.ROOT / "requirements.txt").read_text(),
        "exact_csv_sha256": digest(bench.ROOT / "results/exact/exact-cost-60.csv"),
    }
    (OUT / "protocol.json").write_text(json.dumps(p, indent=1) + "\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            jobs = [{"set": j["set"], "shard": j["shard"]} for j in matrix]
            print("matrix=" + json.dumps(jobs, separators=(",", ":")), file=fh)


def execute_shard(p, name, shard):
    from paper2_controls import EqualTime, PolishOnly, PricingOnly

    h = sources()
    if h != p["sources"]:
        raise ValueError("source hashes changed")
    job = next(j for j in p["jobs"] if j["set"] == name and j["shard"] == shard)
    cache = stored(h)
    selected = set(p["cohorts"][name]["controls"])
    bp = {"set": name, "algos": STANDARD, "workers": 1, "reps": 1}
    bench._init_worker(bp, str(Path("data") / name))
    state = bench._W
    path = OUT / f"rows-{name}-{shard}.csv"
    # A retry of failed jobs downloads this shard from the same workflow run.
    # Retain complete cases. Re-measure a partial paired case on one machine.
    previous = defaultdict(list)
    if path.exists():
        for row in bench.read_store(path):
            if (
                row["set"] == name
                and row["source_sha256"] == h.get(row["algo"])
                and validated(row)
            ):
                previous[row["instance_id"]].append(row)
    # Keep the downloaded checkpoint intact until the replacement is ready.
    resumed_path = path.with_suffix(".resume")
    complete = set()
    with resumed_path.open("w", newline="") as resumed:
        writer = csv.DictWriter(resumed, fieldnames=FIELDS)
        writer.writeheader()
        for i in job["ids"]:
            rr = previous.get(i, ())
            expected = set(STANDARD) | (set(CONTROL) if i in selected else set())
            if len(rr) == len(expected) and {r["algo"] for r in rr} == expected:
                writer.writerows(rr)
                complete.add(i)
    resumed_path.replace(path)
    with path.open("a", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=FIELDS)
        for i in job["ids"]:
            if i in complete:
                continue
            paired = i in selected
            # Co-locate v2 and v3 on paired cases, even when a stored v2 exists.
            todo = [
                n for n in STANDARD if (i, n) not in cache or (paired and n in (V2, V3))
            ]
            rows = (
                bench._run_instance({"instance_id": i, "algos": todo}) if todo else []
            )
            for r in rows:
                previous = cache.get((i, r["algo"]))
                if previous and r.get("schedule_sha256") != previous["schedule_sha256"]:
                    raise ValueError(f"replay mismatch: {i} {r['algo']}")
            for n in STANDARD:
                if n not in todo:
                    rows.append(dict(cache[i, n], origin="stored"))

            def save(row):
                row.update(set=name, case_study=paired)
                row.setdefault("origin", "fresh")
                w.writerow(row)
                fp.flush()
                if not validated(row):
                    raise ValueError(
                        f"invalid result: {name}/{i}/{row['algo']} {row.get('error')}"
                    )

            for row in rows:
                save(row)
            if paired:
                limit = int(next(r for r in rows if r["algo"] == V3)["runtime_ns"])
                equal = EqualTime(limit)
                for n, scheduler in zip(CONTROL, (PricingOnly(), PolishOnly(), equal)):
                    state["schedulers"][n] = scheduler
                    state["reg"][n] = {
                        "label": n,
                        "role": "control",
                        "source_sha256": h[n],
                    }
                for row in bench._run_instance({"instance_id": i, "algos": CONTROL}):
                    if row["algo"] == "equal-time-v2":
                        row.update(
                            budget_time_ns=limit,
                            available_by_cutoff=equal.available,
                            extra_split_trials=equal.trials,
                        )
                    save(row)
            print(f"{name} {i} ({len(todo)} fresh main runs)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    run = sub.add_parser("shard")
    run.add_argument("set", choices=SETS)
    run.add_argument("number", type=int)
    sub.add_parser("report")
    args = parser.parse_args()
    if args.command == "plan":
        return plan()
    protocol = json.loads((OUT / "protocol.json").read_text())
    if args.command == "shard":
        return execute_shard(protocol, args.set, args.number)
    from paper2_report import report

    return report(protocol)


if __name__ == "__main__":
    sys.exit(main())
