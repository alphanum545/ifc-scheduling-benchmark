#!/usr/bin/env python3
"""Minimisation study for DCR-Min (makespan under budget, cost under deadline).

  python3 tools/minimise.py run --data data/dev --suite all --out results/minimise/dev.csv [--shard k --shards n]
  python3 tools/minimise.py report --inputs "results/minimise/dev*.csv" --out results/minimise/summary.md

`run` executes, per instance:
  dcr-v4-rescue      the frozen joint-feasibility DCR (instance D and B)
  dcr-min-makespan   minimise makespan s.t. cost <= B
  dcr-min-cost       minimise cost s.t. makespan <= D
Every schedule is built and re-checked by the pinned Dataset evaluator (build_schedule +
evaluate_schedule), exactly as tools/bench.py does; a run whose two evaluations disagree is
marked invalid. Lower bounds LB_T and LB_C come from algorithms.dcr_min.lower_bounds.

`report` compares against the stored comparator runs in results/store/ for the same instance
(same D and B), restricted to comparators whose schedule respects the relevant constraint.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIELDS = ["algo", "instance_id", "family", "tasks", "qos", "valid", "makespan_us", "compute_cost_ncu",
          "deadline_us", "budget_ncu", "deadline_met", "budget_met", "joint_feasible",
          "makespan_lb_us", "cost_lb_deadline_ncu", "t_fast_us", "cost_floor_ref_ncu",
          "witness_makespan_us", "witness_cost_ncu", "probes", "status", "runtime_s"]


def _instances(suite: str) -> list[dict]:
    man = json.loads((ROOT / "manifests" / "dev-v1.json").read_text())
    entries = man["entries"]
    if suite != "all":
        suite_doc = json.loads((ROOT / "manifests" / "suites" / f"{suite}.json").read_text())
        ids = {x.get("instance_id", x.get("candidate_id")) if isinstance(x, dict) else x for x in suite_doc["entries"]}
        entries = [e for e in entries if e["instance_id"] in ids]
    return sorted(entries, key=lambda e: e["instance_id"]), {b["base_instance_id"]: b for b in man["base_entries"]}


def cmd_run(a) -> int:
    from generator.schedule import build_schedule, evaluate_schedule
    from algorithms.common.interface import AlgorithmInput
    from algorithms.dcr_ifc_v4_rescue import DCRV4RescueScheduler
    from algorithms.dcr_min import DCRMinCostScheduler, DCRMinMakespanScheduler, lower_bounds

    algos = {"dcr-v4-rescue": DCRV4RescueScheduler(), "dcr-min-makespan": DCRMinMakespanScheduler(),
             "dcr-min-cost": DCRMinCostScheduler()}
    entries, bases = _instances(a.suite)
    entries = entries[a.shard::a.shards]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        with out.open() as f:
            done = {(r["algo"], r["instance_id"]) for r in csv.DictReader(f)}
    new = not out.exists()
    with out.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        data = Path(a.data)
        for k, e in enumerate(entries):
            base = json.loads((data / bases[e["base_instance_id"]]["path"]).read_text())
            qos = json.loads((data / e["path"]).read_text())
            inp = AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split="development")
            lb = lower_bounds(inp)
            for name, sch in algos.items():
                if (name, e["instance_id"]) in done:
                    continue
                t0 = time.perf_counter()
                dec = sch.schedule(inp)
                rt = time.perf_counter() - t0
                ev = build_schedule(base, task_order=dec.task_order, resource_assignments=dec.resource_assignments,
                                    deadline_us=inp.deadline_us, budget_ncu=inp.budget_ncu)
                chk = evaluate_schedule(base, ev.schedule, deadline_us=inp.deadline_us, budget_ncu=inp.budget_ncu)
                valid = all(ev.schedule[m] == chk.schedule[m] for m in ("makespan_us", "compute_cost_ncu"))
                st = dec.internal_statistics
                w.writerow({
                    "algo": name, "instance_id": e["instance_id"], "family": e["family"],
                    "tasks": e["target_task_count"], "qos": e["qos_profile"], "valid": valid,
                    "makespan_us": ev.schedule["makespan_us"], "compute_cost_ncu": ev.schedule["compute_cost_ncu"],
                    "deadline_us": inp.deadline_us, "budget_ncu": inp.budget_ncu,
                    "deadline_met": ev.deadline_feasible, "budget_met": ev.budget_feasible,
                    "joint_feasible": ev.joint_feasible, "makespan_lb_us": lb["makespan_lb_us"],
                    "cost_lb_deadline_ncu": lb["cost_lb_deadline_ncu"],
                    # evaluation-only references from the hidden QoS calibration (never seen by a scheduler)
                    "t_fast_us": qos["deadline"]["t_fast_us"], "cost_floor_ref_ncu": qos["budget"]["cost_floor_ref_ncu"],
                    "witness_makespan_us": qos["joint_feasibility_witness"]["makespan_us"],
                    "witness_cost_ncu": qos["joint_feasibility_witness"]["compute_cost_ncu"], "probes": len(st.get("dcrmin_probes", [])) or 1,
                    "status": st.get("dcrmin_status", ""), "runtime_s": f"{rt:.3f}",
                })
                f.flush()
            print(f"[{k + 1}/{len(entries)}] {e['instance_id']}", flush=True)
    return 0


# ---------------------------------------------------------------- report

def _num(r, k):
    return int(r[k])


def _store(algo: str) -> dict[str, dict]:
    p = ROOT / "results" / "store" / f"{algo}.csv"
    if not p.exists():
        return {}
    with p.open() as f:
        return {r["instance_id"]: r for r in csv.DictReader(f) if r["status"] == "ok" and r["valid"] == "True"}


def _med(xs):
    return statistics.median(xs) if xs else float("nan")


def _q(xs, q):
    if not xs:
        return float("nan")
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1) + 0.5))]


def _gm(xs):
    import math
    return math.exp(sum(map(math.log, xs)) / len(xs)) if xs else float("nan")


COMPARATORS = ["bdc", "bdheft", "bdsd", "dbcs", "bddc", "heft-ifc", "peft-ifc", "dcr-v1-admission"]


def _objective_table(L, ids, by, store, *, ours, metric, ref, ok, label_ok, fmt):
    """One table: objective / reference for every algorithm, constraint-respecting runs only."""
    L.append(f"| Algorithm | {label_ok} | geo-mean ratio | median | p90 | DCR-Min better / tie / worse |")
    L.append("|---|---:|---:|---:|---:|---:|")

    def row(name, get, is_ours=False):
        ratios, w, t, l = [], 0, 0, 0
        for i in ids:
            r, o = get(i), by[i][ours]
            if r is None or not ok(r):
                if not is_ours and ok(o):
                    w += 1  # DCR-Min respects the constraint, the other does not
                continue
            ratios.append(int(r[metric]) / int(r[ref]))
            if not is_ours:
                if not ok(o):
                    l += 1
                else:
                    v, mine = int(r[metric]), int(o[metric])
                    w += mine < v; t += mine == v; l += mine > v
        n = sum(1 for i in ids if get(i) is not None and ok(get(i)))
        cmp = "—" if is_ours else f"{w} / {t} / {l}"
        return (f"| {name} | {n}/{len(ids)} | {fmt.format(_gm(ratios))} | "
                f"{fmt.format(_med(ratios))} | {fmt.format(_q(ratios, .9))} | {cmp} |")

    L.append(row(f"**DCR-Min ({ours})**", lambda i: by[i][ours], True))
    L.append(row("DCR-v4R, one run (instance D and B)", lambda i: by[i]["dcr-v4-rescue"]))
    for c in COMPARATORS:
        L.append(row(c, lambda i, c=c: (dict(store[c][i], **{ref: by[i][ours][ref]}) if i in store[c] else None)))


def cmd_report(a) -> int:
    rows = []
    for p in sorted(glob.glob(a.inputs)):
        with open(p) as f:
            rows += list(csv.DictReader(f))
    by = {}
    for r in rows:
        by.setdefault(r["instance_id"], {})[r["algo"]] = r
    ids = sorted(i for i, d in by.items() if len(d) == 3 and all(x["valid"] == "True" for x in d.values()))
    store = {c: _store(c) for c in COMPARATORS}
    within_b = lambda r: int(r["compute_cost_ncu"]) <= int(r["budget_ncu"])
    within_d = lambda r: int(r["makespan_us"]) <= int(r["deadline_us"])
    L = ["# DCR-Min: DCR for the two minimisation variants\n",
         f"{len(ids)} dev instances with valid runs of all three DCR variants. Every schedule was built "
         f"and independently re-checked by the pinned Dataset evaluator (all agree: "
         f"{all(r['valid'] == 'True' for r in rows)}). Comparator rows are the stored runs in "
         f"`results/store/` on the same instances (same D and B; they solve the joint problem, not the "
         f"minimisation problem, so they are a reference, not a tuned rival).\n",
         "References (evaluation only, from the hidden QoS calibration; no scheduler sees them): "
         "`t_fast` = makespan of the fastest calibrated reference schedule (budget-agnostic); "
         "`cost_floor` = the calibrated deadline-conditioned cost floor at the instance deadline; "
         "`witness` = the instance's jointly-feasible witness schedule. All ratios: lower is better.\n"]

    L.append("## 1. Minimise makespan subject to cost <= B (instance deadline ignored)\n")
    L.append("Ratio = makespan / t_fast. Only runs with cost <= B count.\n")
    _objective_table(L, ids, by, store, ours="dcr-min-makespan", metric="makespan_us", ref="t_fast_us",
                     ok=within_b, label_ok="cost <= B", fmt="{:.3f}")
    mm = [by[i]["dcr-min-makespan"] for i in ids]
    L.append(f"\nDCR-Min makespan beats the calibration witness (a budget-feasible schedule) on "
             f"{sum(int(r['makespan_us']) < int(r['witness_makespan_us']) for r in mm)}/{len(mm)} instances.\n")

    L.append("## 2. Minimise compute cost subject to makespan <= D (instance budget ignored)\n")
    L.append("Ratio = cost / cost_floor. Only runs with makespan <= D count.\n")
    _objective_table(L, ids, by, store, ours="dcr-min-cost", metric="compute_cost_ncu", ref="cost_floor_ref_ncu",
                     ok=within_d, label_ok="makespan <= D", fmt="{:.4f}")
    mc = [by[i]["dcr-min-cost"] for i in ids]
    L.append(f"\nDCR-Min cost is below the calibrated cost floor on "
             f"{sum(within_d(r) and int(r['compute_cost_ncu']) < int(r['cost_floor_ref_ncu']) for r in mc)}/{len(mc)} "
             f"instances and below the witness cost on "
             f"{sum(within_d(r) and int(r['compute_cost_ncu']) < int(r['witness_cost_ncu']) for r in mc)}/{len(mc)}.\n")

    L.append("## 3. By QoS level (geo-mean ratio; constraint-respecting runs only)\n")
    L.append("| QoS | n | makespan/t_fast DCR-Min | DCR-v4R | cost/floor DCR-Min | DCR-v4R |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for q in ("relaxed", "moderate", "tight"):
        sub = [i for i in ids if by[i]["dcr-v4-rescue"]["qos"] == q]
        g = lambda algo, m, ref, ok: _gm([int(by[i][algo][m]) / int(by[i][algo][ref]) for i in sub if ok(by[i][algo])])
        L.append(f"| {q} | {len(sub)} | {g('dcr-min-makespan', 'makespan_us', 't_fast_us', within_b):.3f} | "
                 f"{g('dcr-v4-rescue', 'makespan_us', 't_fast_us', within_b):.3f} | "
                 f"{g('dcr-min-cost', 'compute_cost_ncu', 'cost_floor_ref_ncu', within_d):.4f} | "
                 f"{g('dcr-v4-rescue', 'compute_cost_ncu', 'cost_floor_ref_ncu', within_d):.4f} |")

    tid = ROOT / "docs" / "proposed" / "dcr_min_tuning" / "tuning_ids.txt"
    tuned = set(tid.read_text().split()) if tid.exists() else set()
    L.append("\n## 4. Tuning instances vs untouched instances (geo-mean ratio; constraint-respecting runs only)\n")
    L.append("The defaults were chosen on the tuning subset, so that subset is in-sample. "
             "`/LB` columns use the certified lower bounds LB_T and LB_C(D), so they are upper bounds on the "
             "true optimality gap.\n")
    L.append("| Subset | n | makespan/t_fast DCR-Min | DCR-v4R | makespan/LB_T DCR-Min | "
             "cost/floor DCR-Min | DCR-v4R | cost/LB_C(D) DCR-Min |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for name, sub in (("tuning", [i for i in ids if i in tuned]), ("untouched", [i for i in ids if i not in tuned])):
        g = lambda algo, m, ref, ok: _gm([int(by[i][algo][m]) / int(by[i][algo][ref]) for i in sub
                                          if ok(by[i][algo]) and int(by[i][algo][ref] or 0) > 0])
        L.append(f"| {name} | {len(sub)} | {g('dcr-min-makespan', 'makespan_us', 't_fast_us', within_b):.3f} | "
                 f"{g('dcr-v4-rescue', 'makespan_us', 't_fast_us', within_b):.3f} | "
                 f"{g('dcr-min-makespan', 'makespan_us', 'makespan_lb_us', within_b):.3f} | "
                 f"{g('dcr-min-cost', 'compute_cost_ncu', 'cost_floor_ref_ncu', within_d):.4f} | "
                 f"{g('dcr-v4-rescue', 'compute_cost_ncu', 'cost_floor_ref_ncu', within_d):.4f} | "
                 f"{g('dcr-min-cost', 'compute_cost_ncu', 'cost_lb_deadline_ncu', within_d):.3f} |")

    L.append("\n## 5. Search effort and runtime (2-core cloud VM, 2 processes, so indicative only)\n")
    L.append("| Algorithm | median probes | max probes | median runtime (s) | max runtime (s) | runtime / DCR-v4R (median) |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for algo in ("dcr-v4-rescue", "dcr-min-makespan", "dcr-min-cost"):
        pr = [int(by[i][algo]["probes"]) for i in ids]
        rt = [float(by[i][algo]["runtime_s"]) for i in ids]
        ratio = [float(by[i][algo]["runtime_s"]) / max(1e-9, float(by[i]["dcr-v4-rescue"]["runtime_s"])) for i in ids]
        L.append(f"| {algo} | {_med(pr)} | {max(pr)} | {_med(rt):.2f} | {max(rt):.2f} | {_med(ratio):.2f} |")
    st = {}
    for i in ids:
        for algo in ("dcr-min-makespan", "dcr-min-cost"):
            st.setdefault(algo, {}).setdefault(by[i][algo]["status"], 0)
            st[algo][by[i][algo]["status"]] += 1
    L.append("\nSearch outcomes: " + "; ".join(f"{k}: {v}" for k, v in st.items()) + "\n")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    r = s.add_parser("run")
    r.add_argument("--data", required=True)
    r.add_argument("--suite", default="all", help="all | smoke5 | core24")
    r.add_argument("--out", required=True)
    r.add_argument("--shard", type=int, default=0)
    r.add_argument("--shards", type=int, default=1)
    q = s.add_parser("report")
    q.add_argument("--inputs", required=True)
    q.add_argument("--out", required=True)
    a = p.parse_args()
    return cmd_run(a) if a.cmd == "run" else cmd_report(a)


if __name__ == "__main__":
    raise SystemExit(main())
