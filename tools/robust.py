#!/usr/bin/env python3
"""Robustness to runtime/bandwidth noise and IoT/fog/cloud placement share (paper 1).

Protocol (docs/proposed/EXPERIMENTS_PAPER1.md, fixed before running):
  For every instance of the set and every enabled algorithm, compute the algorithm's decision
  (task order + mapping) once on the nominal instance. Then, keeping that decision FIXED,
  rebuild the schedule with the pinned evaluator (generator.schedule.build_schedule) on
  perturbed copies of the instance and check the ORIGINAL deadline and budget:
    - every execution time p[t][r] is multiplied by an independent factor U(1-d, 1+d);
      compute cost and compute energy are recomputed from it with the instance's own rules;
    - every network segment bandwidth is multiplied by an independent factor U(1-d, 1+d);
    - d in {0.1, 0.2, 0.3}; K draws per d.
  Draws are seeded by sha256(instance_id, d, k) only, so every algorithm sees exactly the same
  perturbed instances (paired). Nominal rows also record where the schedule placed its tasks:
  task count, busy time and compute cost per tier.

  python3 tools/robust.py run   --data data/dev --set dev --shard 0 --shards 20 --out .work/r-0.csv
  python3 tools/robust.py merge --inputs ".work/r-*.csv" --out results/robustness/dev.csv.gz
"""
from __future__ import annotations

import argparse
import copy
import csv
import glob
import gzip
import hashlib
import json
import multiprocessing as mp
import os
import random
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

DELTAS = (Fraction(1, 10), Fraction(2, 10), Fraction(3, 10))
FIELDS = ["algo", "instance_id", "family", "tasks", "qos", "scale", "scenario", "kind", "delta", "draw",
          "makespan_us", "deadline_us", "compute_cost_ncu", "budget_ncu", "deadline_met", "budget_met",
          "joint_feasible", "iot_tasks", "fog_tasks", "cloud_tasks", "iot_busy_us", "fog_busy_us",
          "cloud_busy_us", "iot_cost", "fog_cost", "cloud_cost", "error"]


def factor(rng: random.Random, d: Fraction) -> Fraction:
    # exact rational factor on a 1e-4 grid in [1-d, 1+d]
    u = Fraction(rng.randrange(0, 20001), 20000)
    return 1 - d + 2 * d * u


def ceil_frac(x: Fraction) -> int:
    return -((-x.numerator) // x.denominator)


def perturb(base: dict, instance_id: str, d: Fraction, k: int) -> dict:
    seed = int.from_bytes(hashlib.sha256(f"robust-v1|{instance_id}|{d}|{k}".encode()).digest()[:8], "big")
    rng = random.Random(seed)
    out = copy.deepcopy(base)
    res = {r["resource_id"]: r for r in base["resources"]}
    for t in sorted(out["execution_time_us"]):
        for r in sorted(out["execution_time_us"][t]):
            p = max(1, ceil_frac(Fraction(out["execution_time_us"][t][r]) * factor(rng, d)))
            out["execution_time_us"][t][r] = p
            out["compute_cost_ncu"][t][r] = -((-int(res[r]["price_ncu_per_second"]) * p) // 1_000_000)
            out["compute_energy_nj"][t][r] = int(res[r]["active_power_mw"]) * p
    for name in sorted(out["network"]["segments"]):
        seg = out["network"]["segments"][name]
        seg["bandwidth_mbps"] = max(1, round(Fraction(seg["bandwidth_mbps"]) * factor(rng, d)))
    return out


_W: dict = {}


def _init(data: str, set_name: str) -> None:
    import bench
    reg = bench.registry()
    man = bench.manifest(set_name)
    algos = [n for n, s in reg.items() if s["enabled"]]
    _W.update(data=Path(data), entries={e["instance_id"]: e for e in man["entries"]},
              bases={b["base_instance_id"]: b for b in man["base_entries"]}, algos=algos,
              sched={n: bench.load_scheduler(reg[n]) for n in algos}, draws=int(os.environ.get("ROBUST_DRAWS", "10")))


def _instance(iid: str) -> list[dict]:
    from algorithms.common.interface import AlgorithmInput
    from generator.schedule import build_schedule
    e = _W["entries"][iid]
    base = json.loads((_W["data"] / _W["bases"][e["base_instance_id"]]["path"]).read_text())
    qos = json.loads((_W["data"] / e["path"]).read_text())
    inp = AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split="development")
    D, B = inp.deadline_us, inp.budget_ncu
    tier = {r["resource_id"]: r["tier"] for r in base["resources"]}
    common = {"instance_id": iid, "family": e["family"], "tasks": e["target_task_count"], "qos": e["qos_profile"],
              "scale": e["resource_scale"], "scenario": e["scenario_profile"], "deadline_us": D, "budget_ncu": B}
    perturbed = [(d, k, perturb(base, iid, d, k)) for d in DELTAS for k in range(_W["draws"])]
    rows = []
    for n in _W["algos"]:
        try:
            dec = _W["sched"][n].schedule(inp)
            ev = build_schedule(base, task_order=dec.task_order, resource_assignments=dec.resource_assignments,
                                deadline_us=D, budget_ncu=B)
        except Exception as exc:  # recorded, never silently dropped
            rows.append({**common, "algo": n, "kind": "nominal", "error": f"{type(exc).__name__}: {exc}"[:200]})
            continue
        share = {f"{t}_{m}": 0 for t in ("iot", "fog", "cloud") for m in ("tasks", "busy_us", "cost")}
        for a in ev.schedule["assignments"]:
            t, r = a["task_id"], a["resource_id"]
            share[f"{tier[r]}_tasks"] += 1
            share[f"{tier[r]}_busy_us"] += int(a["end_us"]) - int(a["start_us"])
            share[f"{tier[r]}_cost"] += int(base["compute_cost_ncu"][t][r])
        s = ev.schedule
        rows.append({**common, **share, "algo": n, "kind": "nominal", "delta": 0, "draw": 0,
                     "makespan_us": s["makespan_us"], "compute_cost_ncu": s["compute_cost_ncu"],
                     "deadline_met": ev.deadline_feasible, "budget_met": ev.budget_feasible,
                     "joint_feasible": ev.joint_feasible, "error": ""})
        for d, k, pb in perturbed:
            try:
                pe = build_schedule(pb, task_order=dec.task_order, resource_assignments=dec.resource_assignments,
                                    deadline_us=D, budget_ncu=B)
                rows.append({**common, "algo": n, "kind": "perturbed", "delta": str(d), "draw": k,
                             "makespan_us": pe.schedule["makespan_us"], "compute_cost_ncu": pe.schedule["compute_cost_ncu"],
                             "deadline_met": pe.deadline_feasible, "budget_met": pe.budget_feasible,
                             "joint_feasible": pe.joint_feasible, "error": ""})
            except Exception as exc:
                rows.append({**common, "algo": n, "kind": "perturbed", "delta": str(d), "draw": k,
                             "error": f"{type(exc).__name__}: {exc}"[:200]})
    return rows


def cmd_run(a) -> int:
    import bench
    man = bench.manifest(a.set)
    ids = sorted((e["instance_id"] for e in man["entries"]),
                 key=lambda i: (-next(e["target_task_count"] for e in man["entries"] if e["instance_id"] == i), i))
    mine = ids[a.shard::a.shards]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    workers = a.workers or os.cpu_count() or 1
    t0 = time.time()
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        with mp.get_context("spawn").Pool(workers, initializer=_init, initargs=(a.data, a.set)) as pool:
            for n, rows in enumerate(pool.imap_unordered(_instance, mine), 1):
                w.writerows(rows)
                fh.flush()
                print(f"  {n}/{len(mine)} instances, {time.time() - t0:.0f}s", flush=True)
    return 0


def cmd_merge(a) -> int:
    rows = []
    for f in sorted(glob.glob(a.inputs)):
        with open(f, newline="") as fh:
            rows += list(csv.DictReader(fh))
    rows.sort(key=lambda r: (r["algo"], r["instance_id"], r["kind"], r["delta"], int(r["draw"] or 0)))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    errs = sum(1 for r in rows if r["error"])
    print(f"merged {len(rows)} rows ({errs} with errors) -> {out}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--data", required=True)
    r.add_argument("--set", default="dev")
    r.add_argument("--shard", type=int, default=0)
    r.add_argument("--shards", type=int, default=1)
    r.add_argument("--workers", type=int, default=0)
    r.add_argument("--out", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--inputs", required=True)
    m.add_argument("--out", required=True)
    a = p.parse_args()
    return {"run": cmd_run, "merge": cmd_merge}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
