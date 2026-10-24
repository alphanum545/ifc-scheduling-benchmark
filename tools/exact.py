#!/usr/bin/env python3
"""Exact joint-feasibility check of small instances with OR-tools CP-SAT (paper 1).

Protocol (docs/proposed/EXPERIMENTS_PAPER1.md, fixed before running): for every 60-task instance of
the dev and expansion sets, decide whether ANY schedule meets both the deadline and the budget.

Model (identical semantics to generator.schedule):
  x[t,r]  task t on resource r (exactly one);  s[t] start, e[t] = s[t] + sum_r p[t,r] x[t,r];
  serial resources: NoOverlap over optional fixed-size intervals (s[t], p[t,r], x[t,r]);
  precedence i->j: s[j] >= e[i] + comm(i,j, tier(i), tier(j)) unless i and j share a resource,
  then s[j] >= e[i]; comm is generator.network.resource_route_metrics for the edge's data bits;
  e[t] <= D for every t;  sum c[t,r] x[t,r] <= B.
Outcome per instance: FEASIBLE (a schedule found, then independently rebuilt with the pinned
evaluator from its start-time order and mapping and required to be jointly feasible),
INFEASIBLE (proved), or UNKNOWN (time limit).

  python3 tools/exact.py run --data-dev data/dev --data-expansion data/expansion --shard 0 --shards 20 --out .work/x-0.csv
  python3 tools/exact.py merge --inputs ".work/x-*.csv" --out results/exact/exact-60.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

TIME_LIMIT_S = 120
WORKERS = 4
FIELDS = ["set", "instance_id", "family", "qos", "scale", "scenario", "status", "verified", "wall_s",
          "makespan_us", "compute_cost_ncu", "deadline_us", "budget_ncu", "error"]


def solve(base: dict, D: int, B: int):
    from ortools.sat.python import cp_model
    from generator.network import resource_route_metrics

    tasks = sorted(base["execution_time_us"])
    res = sorted(r["resource_id"] for r in base["resources"])
    tier = {r["resource_id"]: r["tier"] for r in base["resources"]}
    tiers = sorted(set(tier.values()))
    p, c = base["execution_time_us"], base["compute_cost_ncu"]
    edges = [(d["parent"], d["child"], int(d["data_bits"])) for d in base["dependencies"]]
    rep = {k: [r for r in res if tier[r] == k] for k in tiers}

    m = cp_model.CpModel()
    x = {(t, r): m.NewBoolVar(f"x_{t}_{r}") for t in tasks for r in res}
    s = {t: m.NewIntVar(0, D, f"s_{t}") for t in tasks}
    e = {t: m.NewIntVar(0, D, f"e_{t}") for t in tasks}
    for t in tasks:
        m.AddExactlyOne(x[t, r] for r in res)
        m.Add(e[t] == s[t] + sum(int(p[t][r]) * x[t, r] for r in res))
    for r in res:
        m.AddNoOverlap([m.NewOptionalFixedSizeIntervalVar(s[t], int(p[t][r]), x[t, r], f"iv_{t}_{r}") for t in tasks])
    y = {(t, k): m.NewBoolVar(f"y_{t}_{k}") for t in tasks for k in tiers}
    for t in tasks:
        for k in tiers:
            m.Add(y[t, k] == sum(x[t, r] for r in rep[k]))
    for i, j, bits in edges:
        same = m.NewBoolVar(f"same_{i}_{j}")
        both = []
        for r in res:
            w = m.NewBoolVar(f"w_{i}_{j}_{r}")
            m.AddImplication(w, x[i, r])
            m.AddImplication(w, x[j, r])
            m.AddBoolOr([x[i, r].Not(), x[j, r].Not(), w])
            both.append(w)
        m.Add(same == sum(both))
        m.Add(s[j] >= e[i]).OnlyEnforceIf(same)
        for ki in tiers:
            for kj in tiers:
                a = rep[ki][0]
                b = next((q for q in rep[kj] if q != a), None)
                if b is None:  # only one resource in this tier: a different-resource pair cannot exist
                    continue
                comm = int(resource_route_metrics(base["network"], tier, source_resource_id=a,
                                                  target_resource_id=b, data_bits=bits)["communication_time_us"])
                m.Add(s[j] >= e[i] + comm).OnlyEnforceIf([y[i, ki], y[j, kj], same.Not()])
    m.Add(sum(int(c[t][r]) * x[t, r] for t in tasks for r in res) <= B)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TIME_LIMIT_S
    solver.parameters.num_search_workers = WORKERS
    solver.parameters.random_seed = 0
    st = solver.Solve(m)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        mapping = {t: next(r for r in res if solver.Value(x[t, r])) for t in tasks}
        order = sorted(tasks, key=lambda t: (solver.Value(s[t]), t))
        return "FEASIBLE", order, mapping
    return ("INFEASIBLE" if st == cp_model.INFEASIBLE else "UNKNOWN"), None, None


def instances(data: dict[str, Path]):
    import bench
    out = []
    for set_name, root in data.items():
        man = bench.manifest(set_name)
        bases = {b["base_instance_id"]: b for b in man["base_entries"]}
        for e in man["entries"]:
            if int(e["target_task_count"]) == 60:
                out.append((set_name, e, root / bases[e["base_instance_id"]]["path"], root / e["path"]))
    return sorted(out, key=lambda z: z[1]["instance_id"])


def cmd_run(a) -> int:
    from generator.schedule import build_schedule
    work = instances({"dev": Path(a.data_dev), "expansion": Path(a.data_expansion)})[a.shard::a.shards]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for n, (set_name, e, bp, qp) in enumerate(work, 1):
            base, qos = json.loads(bp.read_text()), json.loads(qp.read_text())
            D, B = int(qos["deadline"]["deadline_us"]), int(qos["budget"]["budget_ncu"])
            row = {"set": set_name, "instance_id": e["instance_id"], "family": e["family"], "qos": e["qos_profile"],
                   "scale": e["resource_scale"], "scenario": e["scenario_profile"], "deadline_us": D,
                   "budget_ncu": B, "error": ""}
            t0 = time.time()
            try:
                status, order, mapping = solve(base, D, B)
                row["status"] = status
                if status == "FEASIBLE":
                    ev = build_schedule(base, task_order=order, resource_assignments=mapping, deadline_us=D, budget_ncu=B)
                    row.update(verified=bool(ev.joint_feasible), makespan_us=ev.schedule["makespan_us"],
                               compute_cost_ncu=ev.schedule["compute_cost_ncu"])
            except Exception as exc:
                row.update(status="ERROR", error=f"{type(exc).__name__}: {exc}"[:200])
            row["wall_s"] = round(time.time() - t0, 1)
            w.writerow(row)
            fh.flush()
            print(f"  {n}/{len(work)} {e['instance_id'][-60:]}: {row['status']} {row.get('verified', '')} {row['wall_s']}s",
                  flush=True)
    return 0


def cmd_merge(a) -> int:
    rows = []
    for f in sorted(glob.glob(a.inputs)):
        with open(f, newline="") as fh:
            rows += list(csv.DictReader(fh))
    rows.sort(key=lambda r: (r["set"], r["instance_id"]))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(f"merged {len(rows)} rows -> {out}: {dict(Counter(r['status'] for r in rows))}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--data-dev", required=True)
    r.add_argument("--data-expansion", required=True)
    r.add_argument("--shard", type=int, default=0)
    r.add_argument("--shards", type=int, default=1)
    r.add_argument("--out", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--inputs", required=True)
    m.add_argument("--out", required=True)
    a = p.parse_args()
    return {"run": cmd_run, "merge": cmd_merge}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
