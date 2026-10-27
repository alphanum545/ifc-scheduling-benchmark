"""Statistical evidence for the joint-feasibility paper, from stored results only.

No scheduler is run. Reads results/store/ and the report case lists.
Usage: python3 stats.py <bench_repo_dir> <out_dir>
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, wilcoxon

from store_rows import load_store_rows

REPO, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20261024)
HEAD = "dcr-v1-admission"
EXT = "dcr-v3-rescue"
COMPARATORS = ["bdc", "bdsd", "dbcs", "bdheft", "bddc", "heft-ifc", "peft-ifc"]
LABEL = {}

rows = load_store_rows(REPO)
sets = {s: {x["instance_id"] for x in csv.DictReader(open(REPO / f"results/reports/{s}-all/results.csv"))}
        for s in ("dev", "expansion")}

data = {"dev": {}, "expansion": {}}
for x in rows:
    LABEL[x["algo"]] = x["label"]
    s = "dev" if x["instance_id"] in sets["dev"] else "expansion" if x["instance_id"] in sets["expansion"] else None
    if s is None or x["status"] != "ok" or x["valid"] != "True":
        continue
    # dev: prefer the sequential reps=2 run (workers blank). Five cases were later re-run for two
    # algorithms in a parallel smoke test; those rows are used for outcomes but not for runtime.
    cur = data[s].setdefault(x["algo"], {}).get(x["instance_id"])
    if cur is None or (cur["workers"] != "" and x["workers"] == ""):
        data[s][x["algo"]][x["instance_id"]] = x

ALGOS = sorted(data["dev"], key=lambda a: -sum(v["joint_feasible"] == "True" for v in data["dev"][a].values()))


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, running = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvals) - rank) * pvals[i]))
        adj[i] = running
    return adj


def boot_median_ci(values, b=10000):
    v = np.asarray(values, dtype=float)
    idx = RNG.integers(0, len(v), size=(b, len(v)))
    meds = np.median(v[idx], axis=1)
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def nearest_rank(values, q):
    v = sorted(values)
    return v[max(0, math.ceil(q * len(v)) - 1)]


def boot_p95_ci(values, b=10000):
    v = np.sort(np.asarray(values, dtype=float))
    idx = RNG.integers(0, len(v), size=(b, len(v)))
    s = np.sort(v[idx], axis=1)
    k = max(0, math.ceil(0.95 * len(v)) - 1)
    return float(np.percentile(s[:, k], 2.5)), float(np.percentile(s[:, k], 97.5))


def feas(s, a, i, key="joint_feasible"):
    return data[s][a][i][key] == "True"


def mcnemar(s, a, b, cases):
    only_a = sum(feas(s, a, i) and not feas(s, b, i) for i in cases)
    only_b = sum(feas(s, b, i) and not feas(s, a, i) for i in cases)
    both = sum(feas(s, a, i) and feas(s, b, i) for i in cases)
    neither = len(cases) - only_a - only_b - both
    n = only_a + only_b
    p = binomtest(only_a, n, 0.5).pvalue if n else 1.0
    return dict(only_a=only_a, only_b=only_b, both=both, neither=neither, p=p,
                delta_pp=100 * (only_a - only_b) / len(cases))


def ratio_block(s, a, b, cases, metric):
    both = [i for i in cases if feas(s, a, i) and feas(s, b, i)]
    r = [int(data[s][a][i][metric]) / int(data[s][b][i][metric]) for i in both]
    if not r:
        return None
    lo, hi = boot_median_ci(r)
    d = [math.log(x) for x in r]
    p = wilcoxon(d).pvalue if any(d) else 1.0
    return dict(n=len(r), median=float(np.median(r)), ci=(lo, hi), wins=sum(x < 1 for x in r),
                ties=sum(x == 1 for x in r), losses=sum(x > 1 for x in r), p=p)


out = {}
md = []
for s in ("dev", "expansion"):
    cases = sorted(set.intersection(*(set(data[s][a]) for a in ALGOS)))
    N = len(cases)
    res = {"cases": N}
    md.append(f"\n# {s} set ({N} instances, every algorithm valid on every case)\n")

    # 1. feasibility with Wilson CIs, plus the deadline-only / budget-only sanity rows
    md.append("## Feasibility with 95% Wilson intervals\n")
    md.append("| Algorithm | Joint | 95% CI | Deadline only | Budget only |\n|---|---:|---|---:|---:|")
    tab = {}
    for a in ALGOS:
        k = sum(feas(s, a, i) for i in cases)
        kd = sum(feas(s, a, i, "deadline_met") for i in cases)
        kb = sum(feas(s, a, i, "budget_met") for i in cases)
        lo, hi = wilson(k, N)
        tab[a] = dict(joint=k, ci=(lo, hi), deadline=kd, budget=kb)
        md.append(f"| {LABEL[a]} | {k} ({100*k/N:.1f}%) | {100*lo:.1f}–{100*hi:.1f}% | {kd} | {kb} |")
    res["feasibility"] = tab

    # 2. exact McNemar, headline vs each comparator, Holm-corrected
    md.append(f"\n## Exact McNemar: {LABEL[HEAD]} vs each comparator (Holm-adjusted)\n")
    md.append("| Against | Only DCR-v1 | Only other | Both | Neither | Δ (pp) | p (exact) | p (Holm) |\n|---|---:|---:|---:|---:|---:|---:|---:|")
    tests = [mcnemar(s, HEAD, b, cases) for b in COMPARATORS]
    for b, t, ph in zip(COMPARATORS, tests, holm([t["p"] for t in tests])):
        t["p_holm"] = ph
        md.append(f"| {LABEL[b]} | {t['only_a']} | {t['only_b']} | {t['both']} | {t['neither']} | "
                  f"{t['delta_pp']:+.1f} | {t['p']:.2e} | {ph:.2e} |")
    res["mcnemar_head"] = dict(zip(COMPARATORS, tests))

    # 3. extension vs headline and vs BDC
    md.append(f"\n## {LABEL[EXT]} (extension)\n")
    md.append("| Comparison | Only first | Only second | Both | p (exact) |\n|---|---:|---:|---:|---:|")
    ext = {}
    for b in (HEAD, "bdc"):
        t = mcnemar(s, EXT, b, cases)
        ext[b] = t
        md.append(f"| {LABEL[EXT]} vs {LABEL[b]} | {t['only_a']} | {t['only_b']} | {t['both']} | {t['p']:.2e} |")
    res["extension"] = ext

    # 4. predeclared mechanism ablation A/B/C (DCR-v1 spec): A = v0-opt capacity-only reserve,
    #    B = corrected reserve in admission only (v1 Admission), C = in admission and ranking (v1)
    md.append("\n## Mechanism ablation predeclared in the DCR-v1 spec\n")
    md.append("A = capacity-only reserve (DCR-v0 optimized), B = child-arrival reserve in admission only "
              "(DCR-v1 Admission), C = in admission and ranking (DCR-v1 full).\n")
    md.append("| Pair | Only first | Only second | Both | p (exact) |\n|---|---:|---:|---:|---:|")
    abl = {}
    for a, b in (("dcr-v1-admission", "dcr-v0-opt"), ("dcr-v1", "dcr-v0-opt"), ("dcr-v1-admission", "dcr-v1"),
                 ("dcr-v0-opt", "dcr-v0"), ("dcr-v0", "bdc")):
        t = mcnemar(s, a, b, cases)
        abl[f"{a}|{b}"] = t
        md.append(f"| {LABEL[a]} vs {LABEL[b]} | {t['only_a']} | {t['only_b']} | {t['both']} | {t['p']:.2e} |")
    res["ablation"] = abl

    # 5. by QoS tightness: headline vs BDC
    md.append(f"\n## {LABEL[HEAD]} vs BDC by QoS level\n")
    md.append("| QoS | n | DCR-v1 | BDC | Only DCR-v1 | Only BDC | p (exact) |\n|---|---:|---:|---:|---:|---:|---:|")
    byq = {}
    for q in ("relaxed", "moderate", "tight"):
        cq = [i for i in cases if data[s][HEAD][i]["qos"] == q]
        t = mcnemar(s, HEAD, "bdc", cq)
        ka = sum(feas(s, HEAD, i) for i in cq)
        kb = sum(feas(s, "bdc", i) for i in cq)
        byq[q] = dict(t, n=len(cq), head=ka, bdc=kb)
        md.append(f"| {q} | {len(cq)} | {ka} | {kb} | {t['only_a']} | {t['only_b']} | {t['p']:.2e} |")
    res["by_qos_vs_bdc"] = byq

    # 6. secondary quality on cases where both are jointly feasible
    md.append(f"\n## Quality when both are jointly feasible: {LABEL[HEAD]} / other (median, 95% bootstrap CI)\n")
    md.append("| Against | Metric | n | Median ratio | 95% CI | DCR better / tie / worse | Wilcoxon p |\n|---|---|---:|---:|---|---|---:|")
    qual = {}
    for b in ("bdc", "bdsd", "dbcs", "bdheft"):
        for metric in ("makespan_us", "compute_cost_ncu"):
            r = ratio_block(s, HEAD, b, cases, metric)
            if r is None:
                continue
            qual[f"{b}|{metric}"] = r
            md.append(f"| {LABEL[b]} | {metric.split('_')[0]} | {r['n']} | {r['median']:.3f} | "
                      f"{r['ci'][0]:.3f}–{r['ci'][1]:.3f} | {r['wins']} / {r['ties']} / {r['losses']} | {r['p']:.1e} |")
    res["quality"] = qual
    out[s] = res

# 7. runtime: only the dev run is usable (one process per machine, 2 repetitions);
#    the expansion run used all cores per machine, so its timings are not reported as evidence.
s = "dev"
cases = sorted(i for i in set.intersection(*(set(data[s][a]) for a in ALGOS))
               if all(data[s][a][i]["workers"] == "" for a in ALGOS))
md.append(f"\n# Runtime ({len(cases)} dev cases) (dev set, GitHub runners, one instance at a time, median of 2 repetitions)\n")
md.append("Paired ratio = algorithm runtime / BDC runtime on the same case and machine. "
          "The expansion run used 4 parallel processes per machine and is excluded from runtime claims.\n")
md.append("| Algorithm | Median ratio | 95% CI | p95 (nearest rank) | 95% CI | max |\n|---|---:|---|---:|---|---:|")
rt = {}
for a in ALGOS:
    if a == "bdc":
        continue
    r = [int(data[s][a][i]["runtime_ns"]) / int(data[s]["bdc"][i]["runtime_ns"]) for i in cases]
    lo, hi = boot_median_ci(r)
    plo, phi = boot_p95_ci(r)
    rt[a] = dict(median=float(np.median(r)), ci=(lo, hi), p95=nearest_rank(r, 0.95), p95_ci=(plo, phi), max=max(r))
    md.append(f"| {LABEL[a]} | {np.median(r):.3f} | {lo:.3f}–{hi:.3f} | {rt[a]['p95']:.3f} | {plo:.3f}–{phi:.3f} | {max(r):.2f} |")
out["runtime_dev"] = rt
mism = sum(data[s][a][i]["cpu"] != data[s]["bdc"][i]["cpu"] for a in ALGOS for i in cases)
md.append(f"\nRows whose CPU model differs from the BDC row of the same case: {mism}.")

(OUT / "statistics.md").write_text("\n".join(md) + "\n")
(OUT / "statistics.json").write_text(json.dumps(out, indent=1, default=float))
print("\n".join(md))
