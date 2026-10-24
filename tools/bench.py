#!/usr/bin/env python3
"""Plan, run and merge IFC scheduling benchmark runs.

  python3 tools/bench.py plan  --algos all --suite all --shards 20
  python3 tools/bench.py run   --data data --shard 3 --out .work/shard-3.csv
  python3 tools/bench.py merge --inputs ".work/shard-*.csv"

Work is split by *instance*: every algorithm selected for an instance runs on the same
machine, in an order that rotates between repetitions, so runtime ratios are paired.
Only runs not already in results/store.csv (same algorithm version, same source hash,
same instance, same repetition count) are planned, unless --force is given.

Policy runtime is timed around Scheduler.schedule() only. The schedule is then built and
scored by the pinned Dataset evaluator (generator.schedule.build_schedule) and re-checked
independently with generator.schedule.evaluate_schedule; a run whose two evaluations
disagree, or whose fingerprint differs between repetitions, is marked invalid /
nondeterministic and never averaged in.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import importlib
import json
import os
import platform
import statistics
import sys
import time
import tomllib
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "results" / "store.csv"
WORK = ROOT / ".work"
sys.path.insert(0, str(ROOT))

FIELDS = [
    "algo", "label", "role", "algorithm_id", "algorithm_version", "source_sha256",
    "instance_id", "family", "tasks", "resource_scale", "scenario", "qos", "replicate",
    "status", "valid", "deterministic", "reps",
    "schedule_id", "schedule_sha256", "makespan_us", "deadline_us", "compute_cost_ncu", "budget_ncu",
    "compute_energy_nj", "network_energy_pj", "deadline_met", "budget_met", "joint_feasible",
    "runtime_ns", "runtime_ns_all", "cpu", "python", "workers", "run_utc", "error",
]
KEY = ("algo", "source_sha256", "instance_id")


# --------------------------------------------------------------------------- registry
def registry() -> dict[str, dict]:
    with open(ROOT / "algorithms.toml", "rb") as fh:
        reg = tomllib.load(fh)
    for name, spec in reg.items():
        spec.setdefault("enabled", True)
        spec["source_sha256"] = source_hash(spec["sources"])
    return reg


def source_hash(sources: list[str]) -> str:
    h = hashlib.sha256()
    files: list[Path] = []
    for s in sources:
        p = ROOT / s
        files += sorted(p.rglob("*.py")) if p.is_dir() else [p]
    for f in sorted(set(files)):
        if "__pycache__" in f.parts:
            continue
        h.update(f.relative_to(ROOT).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def select_algos(arg: str, reg: dict) -> list[str]:
    if arg.strip() in ("", "all"):
        return [k for k, v in reg.items() if v["enabled"]]
    names = [a.strip() for a in arg.split(",") if a.strip()]
    unknown = [n for n in names if n not in reg]
    if unknown:
        raise SystemExit(f"unknown algorithm(s) {unknown}; known: {', '.join(reg)}")
    return names


def load_scheduler(spec: dict):
    return getattr(importlib.import_module(spec["module"]), spec["class"])()


# --------------------------------------------------------------------------- instances
SET_MANIFESTS = {"dev": "dev-v1.json", "expansion": "expansion-v1.json", "unseen": "unseen-v1.json"}


def manifest(set_name: str = "dev") -> dict:
    return json.loads((ROOT / "manifests" / SET_MANIFESTS[set_name]).read_text(encoding="utf-8"))


def select_instances(a: argparse.Namespace) -> list[dict]:
    set_name = getattr(a, "set", "dev") or "dev"
    entries = manifest(set_name)["entries"]
    if a.suite in ("smoke", "core"):
        if set_name != "dev":
            raise SystemExit("--suite smoke/core is defined for the dev set only; use --suite all")
        suite = json.loads((ROOT / "manifests" / "suites" / f"{'smoke5' if a.suite == 'smoke' else 'core24'}.json").read_text())
        ids = {e["candidate_id"] for e in suite["entries"]}
        entries = [e for e in entries if e["instance_id"] in ids]
    elif a.suite != "all":
        raise SystemExit("--suite must be smoke, core or all")

    def keep(value, arg):
        return arg in ("", "all") or str(value) in {x.strip() for x in arg.split(",")}

    entries = [e for e in entries if keep(e["family"], a.families) and keep(e["target_task_count"], a.tasks)
               and keep(e["qos_profile"], a.qos)]
    return sorted(entries, key=lambda e: e["instance_id"])


# --------------------------------------------------------------------------- store
def read_store(path: Path | None = None) -> list[dict]:
    path = path or STORE
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_store(rows: list[dict], path: Path | None = None) -> None:
    path = path or STORE
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: (r["algo"], r["instance_id"]))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# --------------------------------------------------------------------------- plan
def cmd_plan(a: argparse.Namespace) -> int:
    reg = registry()
    algos = select_algos(a.algos, reg)
    instances = select_instances(a)
    done = {(r["algo"], r["source_sha256"], r["instance_id"]) for r in read_store()
            if r["status"] == "ok" and int(r["reps"] or 0) >= a.reps}
    work = []
    for e in instances:
        todo = [n for n in algos if a.force or (n, reg[n]["source_sha256"], e["instance_id"]) not in done]
        if todo:
            work.append({"instance_id": e["instance_id"], "algos": todo, "tasks": e["target_task_count"]})
    shards = max(1, min(a.shards, len(work))) if work else 0
    buckets: list[list] = [[] for _ in range(shards)]
    loads = [0.0] * shards
    for w in sorted(work, key=lambda w: -w["tasks"] ** 1.6 * len(w["algos"])):
        i = min(range(shards), key=lambda k: loads[k])
        buckets[i].append(w)
        loads[i] += w["tasks"] ** 1.6 * len(w["algos"])
    WORK.mkdir(exist_ok=True)
    plan = {"set": a.set, "reps": a.reps, "workers": a.workers, "algos": algos, "shards": buckets,
            "sources": {n: reg[n]["source_sha256"] for n in algos}}
    (WORK / "plan.json").write_text(json.dumps(plan, indent=1))
    runs = sum(len(w["algos"]) for w in work)
    print(f"set        : {a.set}")
    print(f"algorithms : {', '.join(algos)}")
    print(f"instances  : {len(instances)} selected, {len(work)} with work to do")
    print(f"runs       : {runs} new algorithm x instance runs, {a.reps} repetition(s) each, {shards} shard(s)")
    if a.github_output:
        with open(a.github_output, "a") as fh:
            fh.write(f"matrix={json.dumps([{'shard': i} for i in range(shards)])}\n")
            fh.write(f"todo={runs}\n")
    return 0


# --------------------------------------------------------------------------- run
def cpu_name() -> str:
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def run_one(scheduler, inp, base):
    from generator.schedule import build_schedule, evaluate_schedule

    t0 = time.perf_counter_ns()
    decision = scheduler.schedule(inp)
    runtime = time.perf_counter_ns() - t0
    ev = build_schedule(base, task_order=decision.task_order, resource_assignments=decision.resource_assignments,
                        deadline_us=inp.deadline_us, budget_ncu=inp.budget_ncu)
    check = evaluate_schedule(base, ev.schedule, deadline_us=inp.deadline_us, budget_ncu=inp.budget_ncu)
    s, c = ev.schedule, check.schedule
    metrics = ("makespan_us", "compute_cost_ncu", "compute_energy_nj", "network_energy_pj")
    valid = all(s[m] == c[m] for m in metrics) and (ev.joint_feasible, ev.deadline_feasible, ev.budget_feasible) == (
        check.joint_feasible, check.deadline_feasible, check.budget_feasible)
    fp = (s.get("schedule_sha256"), *(s[m] for m in metrics), ev.joint_feasible)
    return runtime, ev, valid, fp


_W: dict = {}


def _init_worker(plan: dict, data: str) -> None:
    """Per-process state: registry, manifest and scheduler objects (created once per worker)."""
    reg = registry()
    man = manifest(plan.get("set", "dev"))
    _W.update(reg=reg, plan=plan, data=Path(data),
              entries={e["instance_id"]: e for e in man["entries"]},
              bases={b["base_instance_id"]: b for b in man["base_entries"]},
              schedulers={n: load_scheduler(reg[n]) for n in plan["algos"]})


def _run_instance(w: dict) -> list[dict]:
    """Run every planned algorithm on one instance, in one process, in rotating order."""
    from algorithms.common.interface import AlgorithmInput

    reg, plan, schedulers = _W["reg"], _W["plan"], _W["schedulers"]
    e = _W["entries"][w["instance_id"]]
    data = _W["data"]
    base = json.loads((data / _W["bases"][e["base_instance_id"]]["path"]).read_text(encoding="utf-8"))
    qos = json.loads((data / e["path"]).read_text(encoding="utf-8"))
    inp = AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split="development")
    samples: dict[str, list] = {n: [] for n in w["algos"]}
    errors: dict[str, str] = {}
    for rep in range(plan["reps"]):
        order = w["algos"] if rep % 2 == 0 else list(reversed(w["algos"]))
        k = rep % len(order)
        order = order[k:] + order[:k]
        for n in order:
            if n in errors:
                continue
            try:
                samples[n].append(run_one(schedulers[n], inp, base))
            except Exception as exc:  # recorded, never averaged in
                errors[n] = f"{type(exc).__name__}: {exc}"[:300]
                traceback.print_exc()
    rows = []
    for n in w["algos"]:
        spec = reg[n]
        row = {
            "algo": n, "label": spec["label"], "role": spec["role"],
            "algorithm_id": schedulers[n].algorithm_id, "algorithm_version": schedulers[n].algorithm_version,
            "source_sha256": spec["source_sha256"], "instance_id": e["instance_id"], "family": e["family"],
            "tasks": e["target_task_count"], "resource_scale": e["resource_scale"], "scenario": e["scenario_profile"],
            "qos": e["qos_profile"], "replicate": e["replicate_id"], "reps": plan["reps"], "cpu": cpu_name(),
            "python": platform.python_version(), "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "deadline_us": inp.deadline_us, "budget_ncu": inp.budget_ncu, "workers": plan.get("workers", 1),
        }
        if n in errors:
            row.update(status="error", valid=False, deterministic=False, error=errors[n])
        else:
            runtimes = [s[0] for s in samples[n]]
            ev = samples[n][0][1]
            sch = ev.schedule
            row.update(
                status="ok", error="",
                valid=all(s[2] for s in samples[n]),
                # with one repetition determinism is not observed here; the replay check covers it
                deterministic=(all(s[3] == samples[n][0][3] for s in samples[n]) if len(samples[n]) > 1
                               else "unchecked"),
                schedule_id=sch["schedule_id"], schedule_sha256=sch.get("schedule_sha256", ""),
                makespan_us=sch["makespan_us"], compute_cost_ncu=sch["compute_cost_ncu"],
                compute_energy_nj=sch["compute_energy_nj"], network_energy_pj=sch["network_energy_pj"],
                deadline_met=ev.deadline_feasible, budget_met=ev.budget_feasible, joint_feasible=ev.joint_feasible,
                runtime_ns=int(statistics.median(runtimes)), runtime_ns_all=" ".join(map(str, runtimes)),
            )
        rows.append(row)
    return rows


def cmd_run(a: argparse.Namespace) -> int:
    import multiprocessing as mp

    reg = registry()
    plan = json.loads((WORK / "plan.json").read_text())
    if plan["sources"] != {n: reg[n]["source_sha256"] for n in plan["algos"]}:
        raise SystemExit("algorithm sources changed since the plan was made; re-plan")
    workers = a.workers or plan.get("workers") or os.cpu_count() or 1
    plan["workers"] = workers
    work = plan["shards"][a.shard]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # resume: keep instances already completed in a previous (interrupted) attempt of this shard
    done = {r["instance_id"] for r in read_store(out)} if out.exists() else set()
    if not out.exists():
        write_store([], out)
    todo = [w for w in work if w["instance_id"] not in done]
    print(f"shard {a.shard}: {len(work)} instances ({len(done)} already done), {workers} worker process(es), "
          f"cpu: {cpu_name()}, cores: {os.cpu_count()}", flush=True)
    # biggest first so the pool stays balanced
    todo.sort(key=lambda w: -w["tasks"])
    finished, bad = len(done), 0
    ctx = mp.get_context("fork")
    with ctx.Pool(workers, initializer=_init_worker, initargs=(plan, a.data), maxtasksperchild=50) as pool:
        for rows in pool.imap_unordered(_run_instance, todo):
            with open(out, "a", newline="", encoding="utf-8") as fh:  # saved as soon as each instance finishes
                csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore").writerows(rows)
            finished += 1
            bad += sum(r["status"] != "ok" or not r["valid"] or r["deterministic"] is False for r in rows)
            print(f"  [{finished}/{len(work)}] {rows[0]['instance_id']}: "
                  + ", ".join(f"{r['algo']}={'J' if r.get('joint_feasible') is True else ('err' if r['status'] != 'ok' else '-')}"
                              for r in rows), flush=True)
    print(f"shard {a.shard} complete: {finished} instances in {out}; {bad} invalid / nondeterministic / failed rows")
    return 0


# --------------------------------------------------------------------------- merge
def cmd_merge(a: argparse.Namespace) -> int:
    rows = {tuple(r[k] for k in KEY): r for r in read_store()}
    new = 0
    for path in sorted(glob.glob(a.inputs)):
        for r in read_store(Path(path)):
            rows[tuple(r[k] for k in KEY)] = r
            new += 1
    write_store(list(rows.values()))
    print(f"merged {new} new rows; store now holds {len(rows)} rows")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("plan")
    pl.add_argument("--algos", default="all")
    pl.add_argument("--set", default="dev", choices=sorted(SET_MANIFESTS),
                    help="dev (160 pilot development cases), expansion (1,890 frozen expansion cases) "
                         "or unseen (2,241 frozen unseen-DAG cases)")
    pl.add_argument("--suite", default="all", help="dev set only: smoke (5), core (24) or all (160)")
    pl.add_argument("--families", default="all")
    pl.add_argument("--tasks", default="all")
    pl.add_argument("--qos", default="all")
    pl.add_argument("--reps", type=int, default=2, help="repetitions per run (>=2 also checks determinism)")
    pl.add_argument("--shards", type=int, default=20)
    pl.add_argument("--workers", type=int, default=0,
                    help="parallel instance processes per shard (0 = all cores). Use 1 for a clean runtime study")
    pl.add_argument("--force", action="store_true")
    pl.add_argument("--github-output")
    r = sub.add_parser("run")
    r.add_argument("--data", default="data")
    r.add_argument("--shard", type=int, default=0)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=0, help="override the plan's worker count (0 = plan / all cores)")
    m = sub.add_parser("merge")
    m.add_argument("--inputs", required=True)
    a = p.parse_args()
    return {"plan": cmd_plan, "run": cmd_run, "merge": cmd_merge}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
