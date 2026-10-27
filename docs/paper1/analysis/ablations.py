"""Ablation analysis from results/store/ (no scheduler is run).

Usage: python3 ablations.py <bench_repo_dir> <out_md>
"""
import csv
import math
import statistics as S
import sys
from pathlib import Path

from scipy.stats import binomtest

from store_rows import load_store_rows

REPO, OUT = Path(sys.argv[1]), Path(sys.argv[2])
CONTROL = "dcr-abl-control"
VARIANTS = ["dcr-abl-no-reserve", "dcr-abl-zero-prices", "dcr-abl-time-rank",
            "dcr-abl-budget-rank", "dcr-abl-weighted-rank"]
LABEL = {"dcr-abl-no-reserve": "No priced reserve (raw cheapest-remaining only)",
         "dcr-abl-zero-prices": "Zero dual prices",
         "dcr-abl-time-rank": "Time-only ranking",
         "dcr-abl-budget-rank": "Budget-only ranking",
         "dcr-abl-weighted-rank": "Weighted-sum ranking (0.5/0.5)",
         CONTROL: "Control (= DCR-v1 Admission)", "dcr-v1-admission": "DCR-v1 Admission", "bdc": "BDC"}


def holm(p):
    order = sorted(range(len(p)), key=lambda i: p[i]); adj = [0.0] * len(p); run = 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (len(p) - k) * p[i])); adj[i] = run
    return adj


rows = load_store_rows(REPO)
md = []
for set_name in ("dev", "expansion"):
    ids = {x["instance_id"] for x in csv.DictReader(open(REPO / f"results/reports/{set_name}-all/results.csv"))}
    d = {}
    for x in rows:
        if x["instance_id"] in ids and x["status"] == "ok" and x["valid"] == "True":
            d.setdefault(x["algo"], {})[x["instance_id"]] = x
    algos = [CONTROL, *VARIANTS, "dcr-v1-admission", "bdc"]
    missing = [a for a in algos if a not in d]
    if missing:
        md.append(f"\n## {set_name}: missing results for {missing}\n"); continue
    cases = sorted(set.intersection(*(set(d[a]) for a in algos)))
    N = len(cases)
    J = lambda a, i: d[a][i]["joint_feasible"] == "True"
    same = sum(d[CONTROL][i]["schedule_sha256"] == d["dcr-v1-admission"][i]["schedule_sha256"] for i in cases)
    md.append(f"\n## {set_name} ({N} instances)\n")
    md.append(f"Control schedule identical to DCR-v1 Admission's stored schedule: **{same}/{N}**.\n")
    md.append("| Variant | Joint feasible | Δ vs control (pp) | Only control | Only variant | p (Holm, 5 variants) | Deadline met | Budget met |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    tests = []
    for a in VARIANTS:
        oc = sum(J(CONTROL, i) and not J(a, i) for i in cases)
        ov = sum(J(a, i) and not J(CONTROL, i) for i in cases)
        tests.append((a, oc, ov, binomtest(oc, oc + ov, 0.5).pvalue if oc + ov else 1.0))
    adj = holm([t[3] for t in tests])
    for a in [CONTROL, "dcr-v1-admission", "bdc"]:
        k = sum(J(a, i) for i in cases)
        md.append(f"| {LABEL[a]} | {k} ({100*k/N:.1f}%) | | | | | {sum(d[a][i]['deadline_met']=='True' for i in cases)} | {sum(d[a][i]['budget_met']=='True' for i in cases)} |")
    kc = sum(J(CONTROL, i) for i in cases)
    for (a, oc, ov, _), p in zip(tests, adj):
        k = sum(J(a, i) for i in cases)
        md.append(f"| {LABEL[a]} | {k} ({100*k/N:.1f}%) | {100*(k-kc)/N:+.1f} | {oc} | {ov} | {p:.1e} | "
                  f"{sum(d[a][i]['deadline_met']=='True' for i in cases)} | {sum(d[a][i]['budget_met']=='True' for i in cases)} |")
    md.append("\nWhere both are jointly feasible, median variant/control ratio:\n")
    md.append("| Variant | n | Makespan | Cost |\n|---|---:|---:|---:|")
    for a in VARIANTS:
        both = [i for i in cases if J(a, i) and J(CONTROL, i)]
        if not both:
            continue
        mk = S.median(int(d[a][i]["makespan_us"]) / int(d[CONTROL][i]["makespan_us"]) for i in both)
        co = S.median(int(d[a][i]["compute_cost_ncu"]) / int(d[CONTROL][i]["compute_cost_ncu"]) for i in both)
        md.append(f"| {LABEL[a]} | {len(both)} | {mk:.3f} | {co:.3f} |")
    md.append("\nJoint feasibility under tight QoS:\n")
    tight = [i for i in cases if d[CONTROL][i]["qos"] == "tight"]
    md.append("| Algorithm | Tight joint feasible |\n|---|---:|")
    for a in [CONTROL, *VARIANTS, "bdc"]:
        md.append(f"| {LABEL[a]} | {sum(J(a, i) for i in tight)}/{len(tight)} |")
OUT.write_text("# Component ablations of DCR-v1 Admission\n" + "\n".join(md) + "\n")
print(OUT.read_text())
