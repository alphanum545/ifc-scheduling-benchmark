#!/usr/bin/env python3
"""Local before/after study for DCR-Cost (paper 2): run registry algorithms on a fixed sample of a set
and compare them with each other and with the stored CI runs.

  python3 tools/dcr_cost_study.py run    --set expansion --data data/expansion --step 12 --workers 2
  python3 tools/dcr_cost_study.py report --set expansion --step 12

Sample (deterministic): every 60-task instance, plus every `--step`-th of the remaining instances in
instance_id order. Runs use tools/bench.py's own per-instance routine, so timing, the pinned evaluator
rebuild and the independent re-check are the same as in the Benchmark workflow. Output rows have the
store's columns and go to results/paper2/dcr-cost-v3-<set>-sample.csv (not to results/store/: the
store holds CI runs only). Instances are processed in a fixed pseudo-random order and saved one by
one, so an interrupted run resumes and a partial file is still an unbiased sample.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import bench  # noqa: E402

OUT_DIR = ROOT / "results" / "paper2"
NEW, OLD = "dcr-cost-v3", "dcr-cost-v2"


def sample(set_name: str, step: int) -> list[dict]:
    entries = sorted(bench.manifest(set_name)["entries"], key=lambda e: e["instance_id"])
    small = [e for e in entries if e["target_task_count"] == 60]
    rest = [e for e in entries if e["target_task_count"] != 60][::step]
    return sorted(small + rest, key=lambda e: hashlib.sha256(e["instance_id"].encode()).hexdigest())


def out_path(set_name: str) -> Path:
    return OUT_DIR / f"dcr-cost-v3-{set_name}-sample.csv"


def cmd_run(a: argparse.Namespace) -> int:
    import multiprocessing as mp

    algos = [x.strip() for x in a.algos.split(",") if x.strip()]
    plan = {"set": a.set, "reps": 1, "workers": a.workers, "algos": algos}
    out = out_path(a.set)
    rows = bench.read_store(out) if out.exists() else []
    done = {r["instance_id"] for r in rows}
    todo = [{"instance_id": e["instance_id"], "algos": algos, "tasks": e["target_task_count"]}
            for e in sample(a.set, a.step) if e["instance_id"] not in done]
    print(f"{len(done)} instances done, {len(todo)} to do, {a.workers} worker(s)", flush=True)
    with mp.get_context("fork").Pool(a.workers, initializer=bench._init_worker, initargs=(plan, a.data)) as pool:
        for k, got in enumerate(pool.imap_unordered(bench._run_instance, todo), 1):
            rows += got
            bench.write_store(rows, out)
            print(f"{k}/{len(todo)} {got[0]['tasks']} tasks", flush=True)
    return 0


def _sign_p(wins: int, losses: int) -> float:
    n, k = wins + losses, min(wins, losses)
    if n == 0:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def _q(values, q):
    values = sorted(values)
    return values[min(len(values) - 1, int(q * len(values)))]


def cmd_report(a: argparse.Namespace) -> int:
    rows = bench.read_store(out_path(a.set))
    reg = bench.registry()
    local = {(r["algo"], r["instance_id"]): r for r in rows if r["status"] == "ok"}
    ids = sorted({i for (n, i) in local if n == NEW})
    planned = len(sample(a.set, a.step))
    stored = {}
    for name in (OLD, "dcr-cost-v1", "icpcp", "prolis-s0"):
        for r in bench.read_store(bench.STORE_DIR / f"{name}.csv"):
            if r["source_sha256"] == reg[name]["source_sha256"] and r["status"] == "ok":
                stored[name, r["instance_id"]] = r
    exact = {}
    with open(ROOT / "results" / "exact" / "exact-cost-60.csv", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["cost_ncu"]:
                exact[r["instance_id"]] = r
    L = [f"Sample: {len(ids)} of {planned} planned instances of `{a.set}` "
         f"(all 60-task instances plus every {a.step}th of the others).", ""]
    new = {i: local[NEW, i] for i in ids}
    cost = lambda r: int(r["compute_cost_ncu"])  # noqa: E731
    ok = lambda r: r["deadline_met"] == "True"  # noqa: E731
    L += [f"- Valid runs (evaluator rebuild equals independent re-check): {NEW} "
          f"{sum(r['valid'] == 'True' for r in new.values())}/{len(ids)}.",
          f"- {NEW} meets D on {sum(ok(r) for r in new.values())}/{len(ids)}."]
    both = [i for i in ids if (OLD, i) in local]
    if both:
        same = sum(all(local[OLD, i][k] == stored[OLD, i][k] for k in ("schedule_sha256", "makespan_us", "compute_cost_ncu"))
                   for i in both if (OLD, i) in stored)
        L.append(f"- Reproduction of the stored CI runs: local {OLD} equals the stored schedule (hash, makespan, "
                 f"cost) on {same}/{sum((OLD, i) in stored for i in both)} instances.")
    L += ["", "### Cost: DCR-Cost v3 ÷ competitor (instances where both meet D)", "",
          "| group | vs | n | median | mean | p10 | v3 wins / ties / losses | sign p |", "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |"]

    def line(group, label, pairs):
        if not pairs:
            return
        ratios = [x / y for x, y in pairs]
        w, t, l_ = sum(x < y for x, y in pairs), sum(x == y for x, y in pairs), sum(x > y for x, y in pairs)
        L.append(f"| {group} | {label} | {len(pairs)} | {statistics.median(ratios):.3f} | {statistics.mean(ratios):.3f} | "
                 f"{_q(ratios, 0.1):.3f} | {w} / {t} / {l_} | {_sign_p(w, l_):.1e} |")

    groups = [("all", ids)] + [(q, [i for i in ids if new[i]["qos"] == q]) for q in ("tight", "moderate", "relaxed")] + \
             [(f"{t} tasks", [i for i in ids if new[i]["tasks"] == str(t)]) for t in (60, 100, 200, 400, 600, 800, 1000)]
    for group, members in groups:
        for name, label in ((OLD, "DCR-Cost v2 (stored CI run)"), ("dcr-cost-v1", "DCR-Cost v1"),
                            ("prolis-s0", "ProLiS (seed 0)"), ("icpcp", "IC-PCP")):
            if group != "all" and name != OLD:
                continue
            line(group, label, [(cost(new[i]), cost(stored[name, i])) for i in members
                                if (name, i) in stored and ok(new[i]) and ok(stored[name, i])])
    L += ["", "### Against CP-SAT (60-task instances; best cost found in 5 min)", "",
          "| method | n | ÷ C* median | mean | p90 | max | proven-optimal n | ÷ C* median there |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for label, src in (("DCR-Cost v3", lambda i: new[i]), ("DCR-Cost v2", lambda i: stored.get((OLD, i)))):
        r_all, r_opt = [], []
        for i in ids:
            r = src(i)
            if i in exact and r is not None and ok(r):
                r_all.append(cost(r) / int(exact[i]["cost_ncu"]))
                if exact[i]["status"] == "OPTIMAL":
                    r_opt.append(r_all[-1])
        if r_all:
            L.append(f"| {label} | {len(r_all)} | {statistics.median(r_all):.3f} | {statistics.mean(r_all):.3f} | "
                     f"{_q(r_all, 0.9):.3f} | {max(r_all):.3f} | {len(r_opt)} | "
                     f"{statistics.median(r_opt) if r_opt else float('nan'):.3f} |")
    L += ["", "### Policy runtime (s), same machine, same run", "",
          "| tasks | n | v2 median | v3 median | v3 ÷ v2 median (paired) | v3 max |", "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for t in (60, 100, 200, 400, 600, 800, 1000):
        m = [i for i in both if new[i]["tasks"] == str(t)]
        if m:
            t2 = [int(local[OLD, i]["runtime_ns"]) / 1e9 for i in m]
            t3 = [int(new[i]["runtime_ns"]) / 1e9 for i in m]
            L.append(f"| {t} | {len(m)} | {statistics.median(t2):.2f} | {statistics.median(t3):.2f} | "
                     f"{statistics.median(x / y for x, y in zip(t3, t2)):.2f} | {max(t3):.2f} |")
    cpus = sorted({r["cpu"] for r in new.values()})
    L += ["", f"CPU: {'; '.join(cpus)}; {new[ids[0]]['workers']} worker process(es); Python {new[ids[0]]['python']}."]
    text = "\n".join(L) + "\n"
    (OUT_DIR / f"dcr-cost-v3-{a.set}-sample.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("run", "report"):
        s = sub.add_parser(name)
        s.add_argument("--set", default="expansion")
        s.add_argument("--step", type=int, default=12)
        if name == "run":
            s.add_argument("--data", required=True)
            s.add_argument("--algos", default=f"{OLD},{NEW}")
            s.add_argument("--workers", type=int, default=1)
    a = p.parse_args()
    return {"run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
