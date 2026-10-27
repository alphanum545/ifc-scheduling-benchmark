"""Analysis of the paper-1 supporting experiments from committed results (no scheduler is run).

Usage: python3 experiments.py <bench_repo> <out_dir> [tuning|grid|robust|exact|unseen ...]
Protocols: docs/proposed/EXPERIMENTS_PAPER1.md in the benchmark repository.
"""
import csv
import gzip
import json
import math
import statistics as S
import sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

from store_rows import load_store_rows

REPO, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
WHAT = sys.argv[3:] or ["tuning", "grid", "robust", "exact", "unseen"]
HEAD, EXT = "dcr-v1-admission", "dcr-v3-rescue"
MAIN12 = ["dcr-v3-rescue", "dcr-v1-admission", "dcr-v1", "dcr-v0", "dcr-v0-opt", "bdc", "bdsd", "dbcs",
          "bdheft", "bddc", "heft-ifc", "peft-ifc"]


def load_store():
    d = defaultdict(dict)
    for x in load_store_rows(REPO):
        if x["status"] == "ok" and x["valid"] == "True":
            d[x["algo"]][x["instance_id"]] = x
    return d


def manifest_ids(name):
    return [e["instance_id"] for e in json.load(open(REPO / f"manifests/{name}-v1.json"))["entries"]]


def J(d, a, i):
    return d[a][i]["joint_feasible"] == "True"


def mcnemar(d, a, b, cases):
    oa = sum(J(d, a, i) and not J(d, b, i) for i in cases)
    ob = sum(J(d, b, i) and not J(d, a, i) for i in cases)
    return oa, ob, (binomtest(oa, oa + ob, 0.5).pvalue if oa + ob else 1.0)


def wilson(k, n, z=1.959964):
    p = k / n; dd = 1 + z * z / n; c = (p + z * z / (2 * n)) / dd
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / dd
    return 100 * (c - h), 100 * (c + h)


def tuning(d):
    md = ["# Tuned comparators\n"]
    fams = {"bdc": ["bdc-w01", "bdc-w03", "bdc", "bdc-w07", "bdc-w09"],
            "bddc": ["bddc-w01", "bddc-w03", "bddc", "bddc-w07", "bddc-w09"],
            "bdheft": ["bdheft-a01", "bdheft-a03", "bdheft", "bdheft-a07", "bdheft-a09"]}
    wlab = ["0.1", "0.3", "0.5", "0.7", "0.9"]
    sets = {s: manifest_ids(s) for s in ("dev", "expansion")}
    for fam, algos in fams.items():
        if not all(a in d for a in algos):
            md.append(f"\n{fam}: results missing\n"); continue
        md.append(f"\n## {fam.upper()} weight sweep (joint feasible)\n")
        md.append("| Set | " + " | ".join(f"w={w}" for w in wlab) + " | DCR-v1 Admission |")
        md.append("|---|" + "---:|" * 6)
        best = {}
        for s, ids in sets.items():
            cases = [i for i in ids if all(i in d[a] for a in algos + [HEAD])]
            ks = [sum(J(d, a, i) for i in cases) for a in algos]
            best[s] = max(range(5), key=lambda k: (ks[k], -abs(k - 2)))
            md.append(f"| {s} ({len(cases)}) | " + " | ".join(f"**{k}**" if j == best[s] else str(k) for j, k in enumerate(ks))
                      + f" | {sum(J(d, HEAD, i) for i in cases)} |")
        cases = [i for i in sets["expansion"] if all(i in d[a] for a in algos + [HEAD])]
        a_dev = algos[best["dev"]]
        oa, ob, p = mcnemar(d, HEAD, a_dev, cases)
        md.append(f"\n- **Honest tuning** (weight picked on dev = {wlab[best['dev']]}): on expansion, DCR-v1 Admission "
                  f"solves {oa} cases it cannot, it solves {ob} DCR cannot (exact McNemar p = {p:.1e}).")
        a_or = algos[best["expansion"]]
        oa, ob, p = mcnemar(d, HEAD, a_or, cases)
        md.append(f"- **Oracle weight on expansion** ({wlab[best['expansion']]}): DCR-only {oa}, comparator-only {ob}, p = {p:.1e}.")
        vb = [i for i in cases if any(J(d, a, i) for a in algos)]
        only_vb = sum(1 for i in vb if not J(d, HEAD, i)); only_d = sum(1 for i in cases if J(d, HEAD, i) and i not in set(vb))
        md.append(f"- **Virtual best over all five weights** (per-instance oracle): {len(vb)}/{len(cases)} "
                  f"vs DCR-v1 Admission {sum(J(d, HEAD, i) for i in cases)}; DCR-only {only_d}, oracle-only {only_vb}.")
    return md


def grid(d):
    md = ["# Deadline x budget tightness grid (ifc-grid-v1)\n"]
    try:
        man = json.load(open(REPO / "manifests/grid-v1.json"))
    except FileNotFoundError:
        return md + ["grid manifest missing"]
    ent = man["entries"]
    algos = [a for a in MAIN12 if a in d]
    cells = defaultdict(list)
    for e in ent:
        cells[(e["deadline_fraction"], e["budget_fraction"])].append(e["instance_id"])
    D = man["deadline_fractions"]; B = man["budget_fractions"]
    have = [i for i in (x["instance_id"] for x in ent) if all(i in d[a] for a in algos)]
    md.append(f"{len(have)}/{len(ent)} instances have valid results for all {len(algos)} algorithms.\n")
    hs = set(have)
    for a in (HEAD, "bdc", EXT, "bdsd"):
        md.append(f"\n## {a}: joint feasible % (rows deadline fraction, columns budget fraction)\n")
        md.append("| α \\ β | " + " | ".join(B) + " |"); md.append("|---|" + "---:|" * len(B))
        for df in D:
            row = []
            for bf in B:
                ids = [i for i in cells[(df, bf)] if i in hs]
                row.append(f"{100*sum(J(d, a, i) for i in ids)/len(ids):.0f}" if ids else "-")
            md.append(f"| {df} | " + " | ".join(row) + " |")
    md.append("\n## DCR-v1 Admission minus BDC (percentage points); * = exact McNemar p < 0.05 (uncorrected)\n")
    md.append("| α \\ β | " + " | ".join(B) + " |"); md.append("|---|" + "---:|" * len(B))
    wins = losses = 0
    for df in D:
        row = []
        for bf in B:
            ids = [i for i in cells[(df, bf)] if i in hs]
            oa, ob, p = mcnemar(d, HEAD, "bdc", ids)
            diff = 100 * (oa - ob) / len(ids)
            wins += diff > 0 and p < 0.05; losses += diff < 0 and p < 0.05
            row.append(f"{diff:+.0f}{'*' if p < 0.05 else ''}")
        md.append(f"| {df} | " + " | ".join(row) + " |")
    md.append(f"\nCells where DCR-v1 Admission is significantly better: {wins}; significantly worse: {losses} (of 25).")
    tot = {a: sum(J(d, a, i) for i in have) for a in algos}
    md.append("\n## Whole grid\n\n| Algorithm | Joint feasible | 95% CI |\n|---|---:|---|")
    for a in sorted(algos, key=lambda a: -tot[a]):
        lo, hi = wilson(tot[a], len(have))
        md.append(f"| {a} | {tot[a]} ({100*tot[a]/len(have):.1f}%) | {lo:.1f}–{hi:.1f}% |")
    # heatmap figure data
    heat = {a: [[100 * sum(J(d, a, i) for i in cells[(df, bf)] if i in hs) / max(1, len([i for i in cells[(df, bf)] if i in hs]))
                 for bf in B] for df in D] for a in (HEAD, "bdc", EXT)}
    (OUT / "grid_heatmap.json").write_text(json.dumps({"deadline": D, "budget": B, "rates": heat}))
    return md


def robust():
    md = ["# Robustness to noise and IoT/fog/cloud placement (dev)\n"]
    p = REPO / "results/robustness/dev.csv.gz"
    if not p.exists():
        return md + ["robustness results missing"]
    rows = list(csv.DictReader(gzip.open(p, "rt", newline="")))
    errs = [r for r in rows if r["error"]]
    md.append(f"{len(rows)} rows, {len(errs)} with errors.\n")
    nom = {(r["algo"], r["instance_id"]): r for r in rows if r["kind"] == "nominal" and not r["error"]}
    per = defaultdict(list)
    for r in rows:
        if r["kind"] == "perturbed" and not r["error"]:
            per[(r["algo"], r["delta"])].append(r)
    algos = [a for a in MAIN12 if any(k[0] == a for k in nom)]
    deltas = sorted({k[1] for k in per}, key=Fraction)
    md.append("## Joint feasibility under noise (% of all dev instances, mean over draws)\n")
    md.append("| Algorithm | nominal | " + " | ".join(f"±{float(Fraction(x))*100:.0f}%" for x in deltas)
              + " | kept feasible at ±10% / ±20% / ±30% (of nominally feasible) |")
    md.append("|---|---:|" + "---:|" * len(deltas) + "---|")
    for a in algos:
        ids = [i for (b, i) in nom if b == a]
        n0 = sum(nom[(a, i)]["joint_feasible"] == "True" for i in ids)
        cells, kept = [], []
        for dl in deltas:
            rs = per[(a, dl)]
            cells.append(f"{100*sum(r['joint_feasible']=='True' for r in rs)/max(1,len(rs)):.1f}")
            feas = [r for r in rs if nom[(a, r["instance_id"])]["joint_feasible"] == "True"]
            kept.append(f"{100*sum(r['joint_feasible']=='True' for r in feas)/max(1,len(feas)):.0f}%")
        md.append(f"| {a} | {100*n0/len(ids):.1f} | " + " | ".join(cells) + f" | {' / '.join(kept)} |")
    md.append("\n## Median makespan / deadline under ±20% noise (nominally feasible schedules)\n")
    md.append("| Algorithm | median | p90 |\n|---|---:|---:|")
    for a in algos:
        v = sorted(int(r["makespan_us"]) / int(r["deadline_us"]) for r in per[(a, "1/5")]
                   if nom[(a, r["instance_id"])]["joint_feasible"] == "True")
        if v:
            md.append(f"| {a} | {S.median(v):.3f} | {v[int(0.9*(len(v)-1))]:.3f} |")
    md.append("\n## Placement of nominal schedules (share of tasks / busy time / compute cost, %)\n")
    md.append("| Algorithm | IoT | Fog | Cloud |\n|---|---|---|---|")
    for a in algos:
        ids = [i for (b, i) in nom if b == a]
        tot = {m: sum(int(nom[(a, i)][f"{t}_{m}"]) for i in ids for t in ("iot", "fog", "cloud")) for m in ("tasks", "busy_us", "cost")}
        cell = lambda t: " / ".join(f"{100*sum(int(nom[(a, i)][f'{t}_{m}']) for i in ids)/max(1,tot[m]):.0f}" for m in ("tasks", "busy_us", "cost"))
        md.append(f"| {a} | {cell('iot')} | {cell('fog')} | {cell('cloud')} |")
    return md


def exact(d):
    md = ["# Exact CP-SAT feasibility of 60-task instances\n"]
    p = REPO / "results/exact/exact-60.csv"
    if not p.exists():
        return md + ["exact results missing"]
    rows = list(csv.DictReader(open(p, newline="")))
    from collections import Counter
    md.append(f"Statuses: {dict(Counter(r['status'] for r in rows))}. Found schedules verified by the evaluator: "
              f"{sum(r['verified']=='True' for r in rows)}/{sum(r['status']=='FEASIBLE' for r in rows)}.\n")
    md.append("| Algorithm | solved | of proved-feasible solved | failures proved infeasible | failures on feasible | failures unknown |")
    md.append("|---|---:|---:|---:|---:|---:|")
    st = {r["instance_id"]: r["status"] for r in rows}
    feas = [i for i, s in st.items() if s == "FEASIBLE"]
    for a in [EXT, HEAD, "bdc", "bdsd", "dbcs", "bdheft", "bddc"]:
        if a not in d:
            continue
        ids = [i for i in st if i in d[a]]
        sol = [i for i in ids if J(d, a, i)]
        fail = [i for i in ids if not J(d, a, i)]
        md.append(f"| {a} | {len(sol)}/{len(ids)} | {sum(J(d,a,i) for i in feas if i in d[a])}/{len(feas)} | "
                  f"{sum(st[i]=='INFEASIBLE' for i in fail)} | {sum(st[i]=='FEASIBLE' for i in fail)} | "
                  f"{sum(st[i]=='UNKNOWN' for i in fail)} |")
    bad = [i for i, s in st.items() if s == "INFEASIBLE" and any(a in d and i in d[a] and J(d, a, i) for a in MAIN12)]
    md.append(f"\nConsistency check: instances proved infeasible but solved by some heuristic: {len(bad)} (must be 0).")
    return md


def unseen(d):
    md = ["# Unseen-workflow test (ifc-unseen-v1)\n"]
    try:
        man = json.load(open(REPO / "manifests/unseen-v1.json"))
    except FileNotFoundError:
        return md + ["manifest missing"]
    ent = {e["instance_id"]: e for e in man["entries"]}
    algos = [a for a in MAIN12 if a in d]
    cases = [i for i in ent if all(i in d[a] for a in algos)]
    N = len(cases)
    md.append(f"{N}/{len(ent)} instances with valid results for all {len(algos)} algorithms.\n")
    md.append("| Algorithm | Joint feasible | 95% CI | Deadline met | Budget met |\n|---|---:|---|---:|---:|")
    for a in sorted(algos, key=lambda a: -sum(J(d, a, i) for i in cases)):
        k = sum(J(d, a, i) for i in cases); lo, hi = wilson(k, N)
        md.append(f"| {a} | {k} ({100*k/N:.1f}%) | {lo:.1f}–{hi:.1f}% | "
                  f"{sum(d[a][i]['deadline_met']=='True' for i in cases)} | {sum(d[a][i]['budget_met']=='True' for i in cases)} |")
    md.append("\n## DCR-v1 Admission vs each comparator (exact McNemar, Holm over 7)\n")
    md.append("| Against | Only DCR-v1 | Only other | p (Holm) |\n|---|---:|---:|---:|")
    comps = ["bdc", "bdsd", "dbcs", "bdheft", "bddc", "heft-ifc", "peft-ifc"]
    tests = [mcnemar(d, HEAD, b, cases) for b in comps]
    order = sorted(range(len(tests)), key=lambda k: tests[k][2]); adj = [0] * len(tests); run = 0
    for r, k in enumerate(order):
        run = max(run, min(1, (len(tests) - r) * tests[k][2])); adj[k] = run
    for b, t, pa in zip(comps, tests, adj):
        md.append(f"| {b} | {t[0]} | {t[1]} | {pa:.1e} |")
    oa, ob, p = mcnemar(d, EXT, HEAD, cases)
    md.append(f"\nDCR-v3 Rescue vs DCR-v1 Admission: only v3 {oa}, only v1 {ob}, p = {p:.1e}.")
    for dim, key in (("family", "family"), ("source kind", "source_kind"), ("QoS", "qos_profile"), ("tasks", "target_task_count")):
        vals = sorted({ent[i][key] for i in cases}, key=str)
        md.append(f"\n## By {dim}\n")
        md.append(f"| {dim} | n | " + " | ".join([EXT, HEAD, "bdc", "bdsd"]) + " | DCR-v1 vs BDC (only/only) |")
        md.append("|---|---:|" + "---:|" * 5)
        for v in vals:
            ids = [i for i in cases if ent[i][key] == v]
            oa, ob, _ = mcnemar(d, HEAD, "bdc", ids)
            md.append(f"| {v} | {len(ids)} | " + " | ".join(f"{100*sum(J(d,a,i) for i in ids)/len(ids):.1f}%"
                      for a in [EXT, HEAD, "bdc", "bdsd"]) + f" | {oa}/{ob} |")
    both = [i for i in cases if J(d, HEAD, i) and J(d, "bdc", i)]
    if both:
        r = [int(d[HEAD][i]["makespan_us"]) / int(d["bdc"][i]["makespan_us"]) for i in both]
        c = [int(d[HEAD][i]["compute_cost_ncu"]) / int(d["bdc"][i]["compute_cost_ncu"]) for i in both]
        md.append(f"\nWhere both feasible (n={len(both)}): DCR-v1/BDC median makespan {S.median(r):.3f}, cost {S.median(c):.3f}.")
    return md


d = load_store()
for w in WHAT:
    md = {"tuning": lambda: tuning(d), "grid": lambda: grid(d), "robust": robust,
          "exact": lambda: exact(d), "unseen": lambda: unseen(d)}[w]()
    (OUT / f"{w}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md)); print()
