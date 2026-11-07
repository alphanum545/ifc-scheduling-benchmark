#!/usr/bin/env python3
"""Exact deadline-constrained cost minimization on small instances with OR-tools CP-SAT (paper 2).

Purpose: obtain the optimal cost C* (or the solver's proven bound) for every 60-task instance, to measure
how tight the Lagrangian cost bound of tools/cost_bound.py is and how far heuristics are from optimal.
Paper 1's feasibility check (tools/exact.py, results/exact/exact-60.csv) is left unchanged.

Model: the same scheduling semantics as tools/exact.py (one resource per task, serial resources via
NoOverlap of optional intervals, tier-route communication unless both tasks share a resource, every
task finishing by D), with the budget constraint REMOVED and the objective
    minimize  sum_t sum_r c[t,r] x[t,r].
Two valid aids, both recorded in the output:
  * the dataset's joint-feasibility witness (cost C_ref, meets D) is given as a solution hint;
  * the proven Lagrangian bound LB_best is added as the valid cut  cost >= LB_best.
Every found schedule is rebuilt with the pinned evaluator from its start-time order and mapping and
must meet the deadline (verified). Cost depends only on the mapping, so the rebuilt cost is exact.

Outcome: OPTIMAL (C* proven), FEASIBLE (best cost + proven lower bound at the time limit),
INFEASIBLE (impossible: would contradict the witness, so it signals a model error), UNKNOWN.

  python3 tools/exact_cost.py run --data-dev data/dev --data-expansion data/expansion --shard 0 --shards 20 --out .work/xc-0.csv
  python3 tools/exact_cost.py merge --inputs ".work/xc-*.csv" --out results/exact/exact-cost-60.csv
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

TIME_LIMIT_S = 300
WORKERS = 4
FIELDS = ["set", "instance_id", "family", "qos", "scale", "scenario", "status", "verified", "wall_s",
          "cost_ncu", "solver_bound_ncu", "makespan_us", "deadline_us", "C_ref", "LB_best", "LB_sg", "LB_3",
          "C_min", "hint_used", "error"]


def solve(base: dict, D: int, lb: int, witness: dict | None, use_lb_cut: bool = True):
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
                if b is None:
                    continue
                comm = int(resource_route_metrics(base["network"], tier, source_resource_id=a,
                                                  target_resource_id=b, data_bits=bits)["communication_time_us"])
                m.Add(s[j] >= e[i] + comm).OnlyEnforceIf([y[i, ki], y[j, kj], same.Not()])
    cost = sum(int(c[t][r]) * x[t, r] for t in tasks for r in res)
    if use_lb_cut:
        m.Add(cost >= lb)
    m.Minimize(cost)

    hint_used = False
    if witness:
        wa = {a["task_id"]: a for a in witness["assignments"]}
        if set(wa) == set(tasks):
            for t in tasks:
                for r in res:
                    m.AddHint(x[t, r], int(wa[t]["resource_id"] == r))
                m.AddHint(s[t], int(wa[t]["start_us"]))
                m.AddHint(e[t], int(wa[t]["end_us"]))
            hint_used = True

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TIME_LIMIT_S
    solver.parameters.num_search_workers = WORKERS
    solver.parameters.random_seed = 0
    st = solver.Solve(m)
    bound = int(solver.BestObjectiveBound()) if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        mapping = {t: next(r for r in res if solver.Value(x[t, r])) for t in tasks}
        order = sorted(tasks, key=lambda t: (solver.Value(s[t]), t))
        return ("OPTIMAL" if st == cp_model.OPTIMAL else "FEASIBLE"), order, mapping, bound, hint_used
    return ("INFEASIBLE" if st == cp_model.INFEASIBLE else "UNKNOWN"), None, None, None, hint_used


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
    import cost_bound
    data = {"dev": Path(a.data_dev)}
    if a.data_expansion:
        data["expansion"] = Path(a.data_expansion)
    work = instances(data)[a.shard::a.shards]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for n, (set_name, e, bp, qp) in enumerate(work, 1):
            base, qos = json.loads(bp.read_text()), json.loads(qp.read_text())
            D = int(qos["deadline"]["deadline_us"])
            c_ref = int(qos["budget"]["cost_floor_ref_ncu"])
            row = {"set": set_name, "instance_id": e["instance_id"], "family": e["family"], "qos": e["qos_profile"],
                   "scale": e["resource_scale"], "scenario": e["scenario_profile"], "deadline_us": D,
                   "C_ref": c_ref, "error": ""}
            t0 = time.time()
            try:
                b = cost_bound.bounds(cost_bound.load_input(base, qos), c_ref)
                row.update(LB_best=b["LB_best"], LB_sg=b["LB_sg"], LB_3=b["LB_3"], C_min=b["C_min"])
                if a.no_solve:
                    row["status"] = "SKIPPED"
                else:
                    status, order, mapping, bound, hint = solve(base, D, b["LB_best"], qos.get("joint_feasibility_witness"))
                    row.update(status=status, solver_bound_ncu=bound, hint_used=hint)
                    if order is not None:
                        from generator.schedule import build_schedule
                        ev = build_schedule(base, task_order=order, resource_assignments=mapping, deadline_us=D)
                        row.update(verified=bool(ev.schedule["makespan_us"] <= D),
                                   makespan_us=ev.schedule["makespan_us"], cost_ncu=ev.schedule["compute_cost_ncu"])
            except Exception as exc:
                row.update(status="ERROR", error=f"{type(exc).__name__}: {exc}"[:200])
            row["wall_s"] = round(time.time() - t0, 1)
            w.writerow(row)
            fh.flush()
            print(f"  {n}/{len(work)} {e['instance_id'][-60:]}: {row['status']} cost={row.get('cost_ncu', '')} "
                  f"bound={row.get('solver_bound_ncu', '')} LB={row.get('LB_best', '')} C_ref={c_ref} {row['wall_s']}s",
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
    r.add_argument("--data-expansion")
    r.add_argument("--shard", type=int, default=0)
    r.add_argument("--shards", type=int, default=1)
    r.add_argument("--out", required=True)
    r.add_argument("--no-solve", action="store_true", help="compute bounds only (no OR-tools needed)")
    m = sub.add_parser("merge")
    m.add_argument("--inputs", required=True)
    m.add_argument("--out", required=True)
    a = p.parse_args()
    return {"run": cmd_run, "merge": cmd_merge}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
