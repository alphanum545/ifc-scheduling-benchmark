#!/usr/bin/env python3
"""Minimisation study v2: DCR-Min v2 against DCR-v4R and the greedy baselines (dev + expansion).

  python3 tools/minimise_v2.py run --sets dev,expansion --shard k --shards n --workers 0 --out .work/s-k.csv
  python3 tools/minimise_v2.py merge --inputs ".work/s-*.csv" --out results/minimise_v2/runs.csv
  python3 tools/minimise_v2.py report --runs results/minimise_v2/runs.csv [--exact results/minimise_v2/exact.csv]
                                      [--v1 "results/minimise/dev-*.csv"] --out results/minimise_v2/summary.md

Per instance:
  dcr-v4-rescue          one frozen DCR-v4R run at the instance D and B (joint-feasibility reference)
  dcr-min-v2-makespan    min makespan s.t. cost <= B   (also reports its search-only result)
  dcr-min-v2-cost        min cost s.t. makespan <= D   (also reports its search-only result)
  loss1-makespan         LOSS1 from HEFT-IFC (Sakellariou et al., 2007)
  deadline-loss-cost     deadline-LOSS from HEFT-IFC
  dcr-min-makespan/-cost DCR-Min v1 (dev set only), for the v1/v2 comparison
Every schedule is built and re-checked by the pinned Dataset evaluator, as tools/bench.py does.
The unseen set is never touched. Run with --limit N for a smoke test.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import statistics as S
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SETS = {"dev": "dev-v1.json", "expansion": "expansion-v1.json"}
ALGOS = ["dcr-v4-rescue", "dcr-min-v2-makespan", "dcr-min-v2-cost", "loss1-makespan", "deadline-loss-cost"]
V1 = ["dcr-min-makespan", "dcr-min-cost"]  # DCR-Min v1, re-run on the dev set only for the v1/v2 comparison
FIELDS = ["set", "algo", "instance_id", "family", "tasks", "qos", "scale", "scenario", "valid",
          "makespan_us", "compute_cost_ncu", "deadline_us", "budget_ncu", "deadline_met", "budget_met",
          "internal_agrees", "makespan_lb_us", "cost_lb_deadline_ncu", "t_fast_us", "cost_floor_ref_ncu",
          "witness_makespan_us", "witness_cost_ncu", "probes", "status", "search_value", "polish_evals",
          "polish_moves", "runtime_s", "error"]


def _schedulers():
    from algorithms.dcr_ifc_v4_rescue import DCRV4RescueScheduler
    from algorithms.dcr_min import DCRMinCostScheduler, DCRMinMakespanScheduler
    from algorithms.dcr_min_v2 import DCRMinV2CostScheduler, DCRMinV2MakespanScheduler
    from algorithms.greedy_min import DeadlineLossCostScheduler, LOSS1MakespanScheduler
    return {"dcr-v4-rescue": DCRV4RescueScheduler, "dcr-min-v2-makespan": DCRMinV2MakespanScheduler,
            "dcr-min-v2-cost": DCRMinV2CostScheduler, "loss1-makespan": LOSS1MakespanScheduler,
            "deadline-loss-cost": DeadlineLossCostScheduler, "dcr-min-makespan": DCRMinMakespanScheduler,
            "dcr-min-cost": DCRMinCostScheduler}


def work_items(sets: list[str], data_root: Path) -> list[tuple]:
    out = []
    for s in sets:
        man = json.loads((ROOT / "manifests" / SETS[s]).read_text())
        bases = {b["base_instance_id"]: b for b in man["base_entries"]}
        for e in man["entries"]:
            out.append((s, e, str(data_root / s / bases[e["base_instance_id"]]["path"]), str(data_root / s / e["path"])))
    return sorted(out, key=lambda z: (z[0], z[1]["instance_id"]))


def run_instance(item) -> list[dict]:
    from generator.schedule import build_schedule, evaluate_schedule
    from algorithms.common.interface import AlgorithmInput
    from algorithms.dcr_min import lower_bounds
    set_name, e, bp, qp = item
    base, qos = json.loads(Path(bp).read_text()), json.loads(Path(qp).read_text())
    inp = AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split="development")
    lb = lower_bounds(inp)
    common = {"set": set_name, "instance_id": e["instance_id"], "family": e["family"], "tasks": e["target_task_count"],
              "qos": e["qos_profile"], "scale": e.get("resource_scale", ""), "scenario": e.get("scenario_profile", ""),
              "deadline_us": inp.deadline_us, "budget_ncu": inp.budget_ncu, "makespan_lb_us": lb["makespan_lb_us"],
              "cost_lb_deadline_ncu": lb["cost_lb_deadline_ncu"], "t_fast_us": qos["deadline"]["t_fast_us"],
              "cost_floor_ref_ncu": qos["budget"]["cost_floor_ref_ncu"],
              "witness_makespan_us": qos["joint_feasibility_witness"]["makespan_us"],
              "witness_cost_ncu": qos["joint_feasibility_witness"]["compute_cost_ncu"]}
    rows = []
    for name, cls in _schedulers().items():
        if name in V1 and set_name != "dev":
            continue
        row = dict(common, algo=name, error="")
        try:
            t0 = time.perf_counter()
            dec = cls().schedule(inp)
            row["runtime_s"] = f"{time.perf_counter() - t0:.3f}"
            ev = build_schedule(base, task_order=dec.task_order, resource_assignments=dec.resource_assignments,
                                deadline_us=inp.deadline_us, budget_ncu=inp.budget_ncu)
            chk = evaluate_schedule(base, ev.schedule, deadline_us=inp.deadline_us, budget_ncu=inp.budget_ncu)
            st = dec.internal_statistics
            row.update(valid=all(ev.schedule[k] == chk.schedule[k] for k in ("makespan_us", "compute_cost_ncu")),
                       makespan_us=ev.schedule["makespan_us"], compute_cost_ncu=ev.schedule["compute_cost_ncu"],
                       deadline_met=ev.deadline_feasible, budget_met=ev.budget_feasible,
                       internal_agrees=(st.get("internal_makespan_us") in (None, ev.schedule["makespan_us"])),
                       probes=len(st.get("dcrmin_probes", [])), status=st.get("dcrmin_status", ""),
                       search_value=st.get("dcrmin_search_makespan_us" if name.endswith("makespan") else "dcrmin_search_cost_ncu", ""),
                       polish_evals=st.get("dcrmin_polish_evals", st.get("dloss_evals", "")),
                       polish_moves=st.get("dcrmin_polish_moves", st.get("dloss_moves", st.get("loss1_moves", ""))))
        except Exception as exc:  # recorded, never silently dropped
            row.update(valid=False, error=f"{type(exc).__name__}: {exc}"[:300])
        rows.append(row)
    return rows


def cmd_run(a) -> int:
    items = work_items(a.sets.split(","), Path(a.data))[a.shard::a.shards]
    if a.limit:
        items = items[:a.limit]
    # Largest first, so the slowest instances do not land at the end of a worker's queue.
    items.sort(key=lambda z: -int(z[1]["target_task_count"]))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    workers = a.workers or os.cpu_count() or 1
    t0 = time.time()
    with open(out, "w", newline="") as fh, Pool(workers) as pool:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for k, rows in enumerate(pool.imap_unordered(run_instance, items), 1):
            w.writerows(rows)
            fh.flush()
            print(f"[{k}/{len(items)}] {rows[0]['set']} {rows[0]['instance_id'][-70:]} "
                  f"{sum(float(r.get('runtime_s') or 0) for r in rows):.0f}s errors={sum(bool(r['error']) for r in rows)} "
                  f"elapsed {time.time() - t0:.0f}s", flush=True)
    return 0


def cmd_merge(a) -> int:
    rows = [r for p in sorted(glob.glob(a.inputs)) for r in csv.DictReader(open(p, newline=""))]
    rows.sort(key=lambda r: (r["set"], r["instance_id"], (ALGOS + V1).index(r["algo"])))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    n = len({(r["set"], r["instance_id"]) for r in rows})
    print(f"merged {len(rows)} rows, {n} instances, errors {sum(bool(r['error']) for r in rows)} -> {a.out}")
    return 0


# ---------------------------------------------------------------- report

def gm(xs):
    xs = [x for x in xs]
    return math.exp(sum(math.log(max(x, 1e-12)) for x in xs) / len(xs)) if xs else float("nan")


def q(xs, k):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(k * (len(xs) - 1) + 0.5))] if xs else float("nan")


def cmd_report(a) -> int:
    rows = list(csv.DictReader(open(a.runs, newline="")))
    by = defaultdict(dict)
    for r in rows:
        by[(r["set"], r["instance_id"])][r["algo"]] = r
    full = {k: d for k, d in by.items() if all(n in d for n in ALGOS) and all(x["valid"] == "True" and not x["error"] for x in d.values())}
    I = lambda r, k: int(r[k])  # noqa: E731
    inB = lambda r: I(r, "compute_cost_ncu") <= I(r, "budget_ncu")  # noqa: E731
    inD = lambda r: I(r, "makespan_us") <= I(r, "deadline_us")  # noqa: E731
    L = ["# DCR-Min v2: minimisation study (dev + expansion)\n",
         f"{len(rows)} runs on {len(by)} instances; {len(full)} instances have valid, error-free runs of all "
         f"{len(ALGOS)} algorithms (errors: {sum(bool(r['error']) for r in rows)}; evaluator build/re-check agree on "
         f"{sum(r['valid'] == 'True' for r in rows)}/{len(rows)}; policy calendar agrees with the evaluator on "
         f"{sum(r['internal_agrees'] == 'True' for r in rows if r['algo'].startswith('dcr'))}/"
         f"{sum(1 for r in rows if r['algo'].startswith('dcr'))} DCR runs).\n",
         "Ratios are geo-means, lower is better: makespan / `t_fast` and cost / `cost_floor` (hidden calibration "
         "references, evaluation only). `search` = DCR-Min v2 before its polish. Constraint-respecting runs only; "
         "a run that breaks the constraint counts as a loss in win/tie/loss.\n"]

    def block(title, keys):
        ks = [k for k in keys if k in full]
        if not ks:
            return
        L.append(f"## {title} ({len(ks)} instances)\n")
        mk = [full[k] for k in ks]
        v2, v4, lo = "dcr-min-v2-makespan", "dcr-v4-rescue", "loss1-makespan"
        L.append("### Min makespan s.t. cost <= B\n")
        L.append("| Method | cost <= B | makespan / t_fast | median | p90 | v2 better / tie / worse |")
        L.append("|---|---:|---:|---:|---:|---:|")
        for name, get in (("**DCR-Min v2**", lambda d: (I(d[v2], "makespan_us"), d[v2])),
                          ("DCR-Min v2 search only", lambda d: (int(d[v2]["search_value"]), d[v2])),
                          ("DCR-v4R, one run", lambda d: (I(d[v4], "makespan_us"), d[v4])),
                          ("LOSS1 (from HEFT)", lambda d: (I(d[lo], "makespan_us"), d[lo]))):
            ok = [(get(d)[0] / I(d[v2], "t_fast_us"), get(d)[0], d) for d in mk if inB(get(d)[1])]
            w = sum(1 for d in mk if not inB(get(d)[1]) or I(d[v2], "makespan_us") < get(d)[0])
            t = sum(1 for d in mk if inB(get(d)[1]) and I(d[v2], "makespan_us") == get(d)[0])
            rs = [x[0] for x in ok]
            cmp_ = "—" if name.startswith("**") else f"{w} / {t} / {len(mk) - w - t}"
            L.append(f"| {name} | {len(ok)}/{len(mk)} | {gm(rs):.3f} | {q(rs, .5):.3f} | {q(rs, .9):.3f} | {cmp_} |")
        c2, dl = "dcr-min-v2-cost", "deadline-loss-cost"
        L.append("\n### Min cost s.t. makespan <= D\n")
        L.append("| Method | makespan <= D | cost / cost_floor | median | p90 | v2 better / tie / worse |")
        L.append("|---|---:|---:|---:|---:|---:|")
        for name, get in (("**DCR-Min v2**", lambda d: (I(d[c2], "compute_cost_ncu"), d[c2], True)),
                          ("DCR-Min v2 search only", lambda d: (int(d[c2]["search_value"] or 0), d[c2], d[c2]["status"] == "ok")),
                          ("DCR-v4R, one run", lambda d: (I(d[v4], "compute_cost_ncu"), d[v4], True)),
                          ("deadline-LOSS (from HEFT)", lambda d: (I(d[dl], "compute_cost_ncu"), d[dl], True))):
            okf = lambda d: inD(get(d)[1]) and get(d)[2]  # noqa: E731
            ok = [(get(d)[0] / I(d[c2], "cost_floor_ref_ncu"), d) for d in mk if okf(d)]
            w = sum(1 for d in mk if inD(d[c2]) and (not okf(d) or I(d[c2], "compute_cost_ncu") < get(d)[0]))
            t = sum(1 for d in mk if inD(d[c2]) and okf(d) and I(d[c2], "compute_cost_ncu") == get(d)[0])
            rs = [x[0] for x in ok]
            cmp_ = "—" if name.startswith("**") else f"{w} / {t} / {len(mk) - w - t}"
            L.append(f"| {name} | {len(ok)}/{len(mk)} | {gm(rs):.4f} | {q(rs, .5):.4f} | {q(rs, .9):.4f} | {cmp_} |")
        L.append("\n### By size and QoS (geo-mean ratio; v2 / baseline in brackets)\n")
        L.append("| Group | n | makespan v2 | (v2/v4R) | (v2/LOSS1) | cost v2 | (v2/v4R) | (v2/dLOSS) |")
        L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for gkey in ("tasks", "qos"):
            groups = defaultdict(list)
            for d in mk:
                groups[d[v2][gkey]].append(d)
            for g in sorted(groups, key=lambda x: int(x) if gkey == "tasks" else x):
                ds = groups[g]
                L.append(f"| {gkey}={g} | {len(ds)} | {gm(I(d[v2], 'makespan_us') / I(d[v2], 't_fast_us') for d in ds):.3f} | "
                         f"{gm(I(d[v2], 'makespan_us') / I(d[v4], 'makespan_us') for d in ds):.3f} | "
                         f"{gm(I(d[v2], 'makespan_us') / I(d[lo], 'makespan_us') for d in ds):.3f} | "
                         f"{gm(I(d[c2], 'compute_cost_ncu') / I(d[c2], 'cost_floor_ref_ncu') for d in ds):.4f} | "
                         f"{gm(I(d[c2], 'compute_cost_ncu') / max(1, I(d[v4], 'compute_cost_ncu')) for d in ds if inD(d[v4])):.3f} | "
                         f"{gm(I(d[c2], 'compute_cost_ncu') / max(1, I(d[dl], 'compute_cost_ncu')) for d in ds if inD(d[dl])):.3f} |")
        L.append("\n### Hard constraints and runtime\n")
        L.append(f"- min-makespan cost <= B: {sum(inB(d[v2]) for d in mk)}/{len(mk)}; min-cost makespan <= D: "
                 f"{sum(inD(d[c2]) for d in mk)}/{len(mk)}; deadline-LOSS start (HEFT) meets D: {sum(inD(d[dl]) for d in mk)}/{len(mk)}.")
        L.append(f"- Search status (cost): {dict(Counter(d[c2]['status'] for d in mk))}.")
        for algo in ALGOS:
            rt = [float(d[algo]["runtime_s"]) for d in mk]
            L.append(f"- {algo}: median runtime {q(rt, .5):.2f} s, p90 {q(rt, .9):.1f} s, max {max(rt):.1f} s.")
        for algo in (v2, c2):
            pe = [int(d[algo]["polish_evals"] or 0) for d in mk]
            pm = [int(d[algo]["polish_moves"] or 0) for d in mk]
            L.append(f"- {algo} polish: re-timings median {q(pe, .5)}, max {max(pe)}; moves median {q(pm, .5)}, "
                     f"improved {sum(1 for d in mk if (I(d[algo], 'makespan_us' if algo == v2 else 'compute_cost_ncu') < int(d[algo]['search_value'] or 0)))}/{len(mk)}.")
        L.append("")

    keys = sorted(full)
    block("Dev set", [k for k in keys if k[0] == "dev"])
    block("Expansion set (never used for tuning)", [k for k in keys if k[0] == "expansion"])
    block("Dev + expansion", keys)

    v1 = defaultdict(dict)
    for k, d in full.items():
        for algo in V1:
            if algo in d:
                v1[k[1]][algo] = d[algo]
    for p in sorted(glob.glob(a.v1)) if a.v1 else []:
        for r in csv.DictReader(open(p, newline="")):
            v1[r["instance_id"]].setdefault(r["algo"], r)
    ks = [k for k in keys if k[0] == "dev" and all(x in v1[k[1]] for x in V1)]
    if ks:
        L.append(f"## DCR-Min v2 vs v1 (dev, {len(ks)} instances)\n")
        for obj, a1, a2, col in (("makespan", "dcr-min-makespan", "dcr-min-v2-makespan", "makespan_us"),
                                 ("cost", "dcr-min-cost", "dcr-min-v2-cost", "compute_cost_ncu")):
            r2 = [I(full[k][a2], col) / I(v1[k[1]][a1], col) for k in ks]
            rs = [int(full[k][a2]["search_value"]) / I(v1[k[1]][a1], col) for k in ks]
            L.append(f"- {obj}: v2/v1 geo-mean {gm(r2):.4f} (better / tie / worse {sum(x < 1 for x in r2)} / "
                     f"{sum(x == 1 for x in r2)} / {sum(x > 1 for x in r2)}); v2 search only / v1 {gm(rs):.4f} "
                     f"({sum(x < 1 for x in rs)} / {sum(x == 1 for x in rs)} / {sum(x > 1 for x in rs)}).")
        L.append("")

    if a.exact and Path(a.exact).exists():
        ex = list(csv.DictReader(open(a.exact, newline="")))
        L.append(f"## Exact CP-SAT on the 60-task instances ({len(ex)} rows, dev + expansion)\n")
        L.append("Optimality gap = (DCR-Min v2 - CP-SAT lower bound) / DCR-Min v2, so it bounds how far v2 can be "
                 "from optimal. `best` = the best schedule CP-SAT found (warm-started from v2, so never worse), "
                 "verified by the evaluator.\n")
        for obj in ("makespan", "cost"):
            rs = [r for r in ex if r["objective"] == obj and r["status"] in ("OPTIMAL", "FEASIBLE")]
            if not rs:
                continue
            gap = [max(0.0, (int(r["v2_value"]) - int(r["bound"])) / int(r["v2_value"])) for r in rs if int(r["v2_value"]) > 0]
            imp = [int(r["best_value"]) / int(r["v2_value"]) for r in rs if int(r["v2_value"]) > 0]
            L.append(f"- **{obj}**: statuses {dict(Counter(r['status'] for r in ex if r['objective'] == obj))}; "
                     f"verified {sum(r['verified'] == 'True' for r in rs)}/{len(rs)}. "
                     f"v2 proved optimal on {sum(1 for r in rs if int(r['v2_value']) <= int(r['bound']))}/{len(rs)}. "
                     f"Gap to the CP-SAT bound: median {100 * q(gap, .5):.1f}%, p90 {100 * q(gap, .9):.1f}%, "
                     f"max {100 * max(gap):.1f}%. CP-SAT's best / v2: geo-mean {gm(imp):.4f}, "
                     f"improved on {sum(x < 1 for x in imp)}/{len(imp)}.")
            for qq in ("tight", "moderate", "relaxed"):
                g = [max(0.0, (int(r["v2_value"]) - int(r["bound"])) / int(r["v2_value"])) for r in rs if r["qos"] == qq and int(r["v2_value"]) > 0]
                if g:
                    L.append(f"  - {qq}: n={len(g)}, median gap {100 * q(g, .5):.1f}%, p90 {100 * q(g, .9):.1f}%")
        L.append("")

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    r = s.add_parser("run")
    r.add_argument("--sets", default="dev,expansion")
    r.add_argument("--data", default="data", help="folder holding <set>/ data folders")
    r.add_argument("--shard", type=int, default=0)
    r.add_argument("--shards", type=int, default=1)
    r.add_argument("--workers", type=int, default=0)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--out", required=True)
    m = s.add_parser("merge")
    m.add_argument("--inputs", required=True)
    m.add_argument("--out", required=True)
    q_ = s.add_parser("report")
    q_.add_argument("--runs", required=True)
    q_.add_argument("--exact", default="")
    q_.add_argument("--v1", default="")
    q_.add_argument("--out", required=True)
    a = p.parse_args()
    return {"run": cmd_run, "merge": cmd_merge, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
