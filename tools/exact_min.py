#!/usr/bin/env python3
"""Exact optimality gaps for DCR-Min v2 on the 60-task instances (dev + expansion), OR-tools CP-SAT.

Same scheduling model as tools/exact.py (x[t,r] one resource per task; serial resources via NoOverlap
over optional fixed-size intervals; precedence with route-aware communication unless both tasks share
a resource), with an objective instead of a feasibility question:

  makespan: minimise C_max s.t. sum c[t,r] x[t,r] <= B, horizon = DCR-Min v2's makespan (a feasible
            upper bound), C_max >= LB_T.
  cost:     minimise sum c[t,r] x[t,r] s.t. every e[t] <= D, cost <= DCR-Min v2's cost.

Both are warm-started from DCR-Min v2's plan (assignment and evaluator start times). Outcome per
instance and objective: OPTIMAL, FEASIBLE (time limit, with a proved lower bound) or UNKNOWN. The best
schedule found is rebuilt by the pinned evaluator from its start-time order and mapping. Any CP-SAT
schedule can be left-shifted into one the evaluator builds, so the CP-SAT lower bound is also a lower
bound for every schedule the benchmark can express.

  python3 tools/exact_min.py run --data data --shard 0 --shards 20 --out .work/x-0.csv [--time-limit 120] [--limit N]
  python3 tools/exact_min.py merge --inputs ".work/x-*.csv" --out results/minimise_v2/exact.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIELDS = ["set", "instance_id", "family", "qos", "objective", "status", "verified", "v2_value", "best_value",
          "bound", "lb_simple", "wall_s", "v2_runtime_s", "deadline_us", "budget_ncu", "error"]


def build(base: dict, H: int):
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
    s = {t: m.NewIntVar(0, H, f"s_{t}") for t in tasks}
    e = {t: m.NewIntVar(0, H, f"e_{t}") for t in tasks}
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
    return m, x, s, e, cost, tasks, res


def solve(base, objective, D, B, plan, v2_value, lb_t, time_limit):
    from ortools.sat.python import cp_model
    H = v2_value if objective == "makespan" else D
    m, x, s, e, cost, tasks, res = build(base, H)
    if objective == "makespan":
        cmax = m.NewIntVar(lb_t, H, "cmax")
        for t in tasks:
            m.Add(e[t] <= cmax)
        m.Add(cost <= B)
        m.Minimize(cmax)
    else:
        m.Add(cost <= v2_value)
        m.Minimize(cost)
    assign, starts = plan
    for t in tasks:
        for r in res:
            m.AddHint(x[t, r], 1 if assign[t] == r else 0)
        m.AddHint(s[t], starts[t])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 4
    solver.parameters.random_seed = 0
    st = solver.Solve(m)
    name = {cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE", cp_model.INFEASIBLE: "INFEASIBLE"}.get(st, "UNKNOWN")
    bound = math.ceil(solver.BestObjectiveBound() - 1e-6) if name in ("OPTIMAL", "FEASIBLE") else None
    if name not in ("OPTIMAL", "FEASIBLE"):
        return name, None, None, bound
    mapping = {t: next(r for r in res if solver.Value(x[t, r])) for t in tasks}
    order = sorted(tasks, key=lambda t: (solver.Value(s[t]), t))
    return name, order, mapping, bound


def items(data: Path):
    out = []
    for set_name, man_name in (("dev", "dev-v1.json"), ("expansion", "expansion-v1.json")):
        man = json.loads((ROOT / "manifests" / man_name).read_text())
        bases = {b["base_instance_id"]: b for b in man["base_entries"]}
        for e in man["entries"]:
            if int(e["target_task_count"]) == 60:
                out.append((set_name, e, data / set_name / bases[e["base_instance_id"]]["path"], data / set_name / e["path"]))
    return sorted(out, key=lambda z: (z[0], z[1]["instance_id"]))


def cmd_run(a) -> int:
    from generator.schedule import build_schedule
    from algorithms.common.interface import AlgorithmInput
    from algorithms.dcr_min import lower_bounds
    from algorithms.dcr_min_v2 import DCRMinV2CostScheduler, DCRMinV2MakespanScheduler
    work = items(Path(a.data))[a.shard::a.shards]
    if a.limit:
        work = work[:a.limit]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for n, (set_name, e, bp, qp) in enumerate(work, 1):
            base, qos = json.loads(bp.read_text()), json.loads(qp.read_text())
            inp = AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split="development")
            D, B = inp.deadline_us, inp.budget_ncu
            lb = lower_bounds(inp)
            for objective, cls in (("makespan", DCRMinV2MakespanScheduler), ("cost", DCRMinV2CostScheduler)):
                row = {"set": set_name, "instance_id": e["instance_id"], "family": e["family"], "qos": e["qos_profile"],
                       "objective": objective, "deadline_us": D, "budget_ncu": B, "error": "",
                       "lb_simple": lb["makespan_lb_us"] if objective == "makespan" else lb["cost_lb_deadline_ncu"]}
                t0 = time.time()
                try:
                    dec = cls().schedule(inp)
                    row["v2_runtime_s"] = round(time.time() - t0, 2)
                    ev = build_schedule(base, task_order=dec.task_order, resource_assignments=dec.resource_assignments)
                    sch = ev.schedule
                    v2 = sch["makespan_us"] if objective == "makespan" else sch["compute_cost_ncu"]
                    ok = sch["compute_cost_ncu"] <= B if objective == "makespan" else sch["makespan_us"] <= D
                    row["v2_value"] = v2
                    if not ok:
                        row.update(status="V2_INFEASIBLE")
                    else:
                        plan = (dict(dec.resource_assignments), {x["task_id"]: x["start_us"] for x in sch["assignments"]})
                        t1 = time.time()
                        status, order, mapping, bound = solve(base, objective, D, B, plan, v2, lb["makespan_lb_us"], a.time_limit)
                        row.update(status=status, bound=bound if bound is not None else "", wall_s=round(time.time() - t1, 1))
                        if order is not None:
                            chk = build_schedule(base, task_order=order, resource_assignments=mapping).schedule
                            val = chk["makespan_us"] if objective == "makespan" else chk["compute_cost_ncu"]
                            good = chk["compute_cost_ncu"] <= B if objective == "makespan" else chk["makespan_us"] <= D
                            row.update(verified=bool(good), best_value=min(val, v2) if good else v2)
                except Exception as exc:
                    row.update(status="ERROR", error=f"{type(exc).__name__}: {exc}"[:300])
                w.writerow(row)
                fh.flush()
                print(f"  {n}/{len(work)} {objective:8} {e['instance_id'][-55:]}: {row.get('status')} v2={row.get('v2_value')} "
                      f"best={row.get('best_value')} bound={row.get('bound')} {row.get('wall_s')}s", flush=True)
    return 0


def cmd_merge(a) -> int:
    rows = [r for f in sorted(glob.glob(a.inputs)) for r in csv.DictReader(open(f, newline=""))]
    rows.sort(key=lambda r: (r["set"], r["instance_id"], r["objective"]))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(f"merged {len(rows)} rows -> {a.out}: {dict(Counter((r['objective'], r['status']) for r in rows))}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--data", default="data")
    r.add_argument("--shard", type=int, default=0)
    r.add_argument("--shards", type=int, default=1)
    r.add_argument("--time-limit", type=float, default=120)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--out", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--inputs", required=True)
    m.add_argument("--out", required=True)
    a = p.parse_args()
    return {"run": cmd_run, "merge": cmd_merge}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
