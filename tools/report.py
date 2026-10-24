#!/usr/bin/env python3
"""Build a report (tables + paper figures) from results/store.csv.

  python3 tools/report.py --algos all --highlight dcr-v1-admission --suite all --name dev-all

Writes results/reports/<name>/:
  summary.md      key tables as text (also shown on the Actions run page)
  summary.xlsx    the same tables plus per-run rows, one sheet each
  results.csv     one row per run used in the report
  replay.md       exact-match check against the historical results (tools/verify_replay.py)
  figures/*.pdf, *.png

Only runs made with each algorithm's current source are used. Comparisons are made on
the instances where every selected algorithm has a valid, deterministic run, so all
algorithms are compared on exactly the same cases; the Validity table says what was left out.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import ROOT, manifest, read_store, registry, select_algos  # noqa: E402

DIMENSIONS = [("family", "Workflow family"), ("tasks", "Number of tasks"), ("qos", "QoS tightness"),
              ("scenario", "Scenario"), ("resource_scale", "Resource scale")]
ORDER = {"qos": ["relaxed", "moderate", "tight"],
         "scenario": ["balanced", "compute_constrained", "network_constrained"],
         "resource_scale": ["S01", "S02", "S03"]}

# Reference palette (dataviz skill): highlight = slot-1 blue, other proposed = lighter blue step,
# comparators = neutral grey ramp; gains/losses = blue/orange diverging poles.
HIGHLIGHT = "#2a78d6"
PROPOSED = "#9cc3f0"
COMPARATOR = "#b4b3ad"
GAIN, LOSS = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
LINE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]


def truthy(v) -> bool:
    return str(v) == "True"


def pct(n: int, d: int) -> str:
    return f"{n}/{d} ({100 * n / d:.1f}%)" if d else "-"


def q(values, p):
    v = sorted(values)
    return v[max(0, math.ceil(p * len(v)) - 1)] if v else float("nan")


def md_table(head: list[str], rows: list[list], align: str | None = None) -> list[str]:
    align = align or ("l" + "r" * (len(head) - 1))
    sep = ["---:" if a == "r" else "---" for a in align]
    return ["| " + " | ".join(head) + " |", "| " + " | ".join(sep) + " |"] + \
           ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--algos", default="all")
    p.add_argument("--highlight", default="dcr-v1-admission")
    p.add_argument("--baseline", default="bdc", help="runtime ratios are paired against this algorithm")
    p.add_argument("--set", default="dev", choices=["dev", "expansion", "unseen", "grid"])
    p.add_argument("--suite", default="all")
    p.add_argument("--families", default="all")
    p.add_argument("--tasks", default="all")
    p.add_argument("--qos", default="all")
    p.add_argument("--name", default="latest")
    p.add_argument("--no-figures", action="store_true")
    a = p.parse_args()

    from bench import select_instances  # noqa: E402

    reg = registry()
    algos = select_algos(a.algos, reg)
    hl = a.highlight if a.highlight in algos else None
    base = a.baseline if a.baseline in algos else None
    wanted = {e["instance_id"] for e in select_instances(a)}
    rows = [r for r in read_store() if r["algo"] in algos and r["instance_id"] in wanted
            and r["source_sha256"] == reg[r["algo"]]["source_sha256"]]
    by = {(r["algo"], r["instance_id"]): r for r in rows}

    def good(r):  # one-repetition runs record deterministic="unchecked"; the replay check covers determinism
        return r and r["status"] == "ok" and truthy(r["valid"]) and r["deterministic"] in ("True", "unchecked")

    common = sorted(i for i in wanted if all(good(by.get((n, i))) for n in algos))
    out = ROOT / "results" / "reports" / a.name
    (out / "figures").mkdir(parents=True, exist_ok=True)
    N = len(common)
    lab = {n: reg[n]["label"] for n in algos}
    md = [f"# Report: {a.name}", "",
          f"Instance set: **{a.set}**. Algorithms: {', '.join(lab[n] for n in algos)}. Highlight: {lab.get(hl, 'none')}. "
          f"Cases: {len(wanted)} selected, **{N} compared** (every selected algorithm valid, and deterministic where checked).", ""]

    # ---- validity
    vrows = []
    for n in algos:
        rs = [by.get((n, i)) for i in sorted(wanted)]
        vrows.append([lab[n], sum(r is not None for r in rs), sum(bool(good(r)) for r in rs),
                      sum(r is not None and r["status"] != "ok" for r in rs),
                      sum(r is not None and r["status"] == "ok" and not truthy(r["valid"]) for r in rs),
                      sum(r is not None and r["status"] == "ok" and r["deterministic"] == "False" for r in rs),
                      len(wanted) - sum(r is not None for r in rs)])
    unchecked = sum(r["deterministic"] == "unchecked" for r in rows if r["status"] == "ok")
    if unchecked:
        md += [f"Determinism was not re-observed for {unchecked} one-repetition runs; the replay check against the "
               "historical results covers it.", ""]
    md += ["## Validity", ""] + md_table(["Algorithm", "Runs", "Valid + deterministic", "Errors", "Invalid",
                                           "Nondeterministic", "Missing"], vrows) + [""]

    if N == 0:
        (out / "summary.md").write_text("\n".join(md + ["No case has a valid run for every selected algorithm."]) + "\n")
        print("\n".join(md))
        return 0

    R = {n: [by[(n, i)] for i in common] for n in algos}

    def rt_ratio(n):
        if not base or n == base:
            return []
        return [int(by[(n, i)]["runtime_ns"]) / int(by[(base, i)]["runtime_ns"]) for i in common]

    # ---- headline table
    head = ["Algorithm", "Joint feasible", "Deadline met", "Budget met", "Median runtime (ms)",
            f"Runtime / {lab.get(base, '-')} median", "p95", "max"]
    trows = []
    for n in sorted(algos, key=lambda n: -sum(truthy(r["joint_feasible"]) for r in R[n])):
        rs = R[n]
        rr = rt_ratio(n)
        trows.append([("**" + lab[n] + "**") if n == hl else lab[n],
                      pct(sum(truthy(r["joint_feasible"]) for r in rs), N),
                      pct(sum(truthy(r["deadline_met"]) for r in rs), N),
                      pct(sum(truthy(r["budget_met"]) for r in rs), N),
                      f"{statistics.median(int(r['runtime_ns']) for r in rs) / 1e6:.0f}",
                      f"{statistics.median(rr):.3f}x" if rr else "-",
                      f"{q(rr, .95):.3f}x" if rr else "-", f"{max(rr):.3f}x" if rr else "-"])
    md += ["## Joint deadline-and-budget feasibility", ""] + md_table(head, trows) + [
        "", "Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; "
            "ratios are paired on the same machine and case, p95 is nearest-rank.", ""]

    # ---- by dimension
    for key, title in DIMENSIONS:
        vals = sorted({r[key] for r in R[algos[0]]}, key=lambda v: (ORDER.get(key, []).index(v)
                      if v in ORDER.get(key, []) else 99, int(v) if v.isdigit() else v))
        rows_d = []
        for n in algos:
            cells = []
            for v in vals:
                sub = [r for r in R[n] if r[key] == v]
                cells.append(f"{sum(truthy(r['joint_feasible']) for r in sub)}/{len(sub)}")
            rows_d.append([lab[n]] + cells)
        md += [f"## Joint feasibility by {title.lower()}", ""] + md_table([title] + vals, rows_d) + [""]

    # ---- pairwise vs highlight
    pw = []
    if hl:
        for n in algos:
            if n == hl:
                continue
            gains = sum(truthy(by[(hl, i)]["joint_feasible"]) and not truthy(by[(n, i)]["joint_feasible"]) for i in common)
            losses = sum(truthy(by[(n, i)]["joint_feasible"]) and not truthy(by[(hl, i)]["joint_feasible"]) for i in common)
            both = [i for i in common if truthy(by[(hl, i)]["joint_feasible"]) and truthy(by[(n, i)]["joint_feasible"])]
            ms = [int(by[(hl, i)]["makespan_us"]) / int(by[(n, i)]["makespan_us"]) for i in both]
            cost = [int(by[(hl, i)]["compute_cost_ncu"]) / int(by[(n, i)]["compute_cost_ncu"]) for i in both]
            energy = [(int(by[(hl, i)]["compute_energy_nj"]) * 1000 + int(by[(hl, i)]["network_energy_pj"])) /
                      (int(by[(n, i)]["compute_energy_nj"]) * 1000 + int(by[(n, i)]["network_energy_pj"])) for i in both]
            pw.append([lab[n], gains, losses, len(both),
                       f"{statistics.median(ms):.3f}" if ms else "-", f"{statistics.median(cost):.3f}" if cost else "-",
                       f"{statistics.median(energy):.3f}" if energy else "-"])
        md += [f"## {lab[hl]} against each algorithm", ""] + md_table(
            ["Against", f"Cases only {lab[hl]} is feasible", "Cases only the other is feasible", "Both feasible",
             "Makespan ratio (median)", "Cost ratio (median)", "Energy ratio (median)"], pw) + [
            "", f"Ratios are {lab[hl]} / other on cases where both are jointly feasible; below 1 favours {lab[hl]}. "
                "Energy = compute + network energy.", ""]

    # ---- replay
    subprocess.run([sys.executable, str(ROOT / "tools" / "verify_replay.py"), "--out", str(out / "replay.md")],
                   check=False, stdout=subprocess.DEVNULL)
    if (out / "replay.md").exists():
        rep = (out / "replay.md").read_text().splitlines()
        md += ["## Replay against the historical results", ""] + [l for l in rep if l.startswith("|") or l.startswith("**")] + [""]

    (out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # ---- results.csv
    used = [by[(n, i)] for n in algos for i in common]
    with open(out / "results.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(used[0].keys()))
        w.writeheader()
        w.writerows(used)

    # ---- xlsx
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
        wb = Workbook()
        sheets = [("Feasibility", head, trows), ("Validity", ["Algorithm", "Runs", "Valid + deterministic", "Errors",
                                                                "Invalid", "Nondeterministic", "Missing"], vrows)]
        if pw:
            sheets.append(("Pairwise", ["Against", "Only highlight feasible", "Only other feasible", "Both feasible",
                                        "Makespan ratio", "Cost ratio", "Energy ratio"], pw))
        for i, (name, h, rws) in enumerate(sheets):
            ws = wb.active if i == 0 else wb.create_sheet()
            ws.title = name
            ws.append(h)
            for c in ws[1]:
                c.font = Font(bold=True)
            for r in rws:
                ws.append([str(x).replace("**", "") for x in r])
        ws = wb.create_sheet("Runs")
        ws.append(list(used[0].keys()))
        for r in used:
            ws.append(list(r.values()))
        wb.save(out / "summary.xlsx")
    except ImportError:
        print("openpyxl not installed; summary.xlsx skipped")

    if not a.no_figures:
        figures(out / "figures", algos, hl, base, lab, reg, R, common, by)
    print("\n".join(md))
    return 0


# ============================================================================ figures
def figures(fig_dir, algos, hl, base, lab, reg, R, common, by):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker  # noqa: F401

    plt.rcParams.update({
        "font.family": "serif", "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#8a8984",
        "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
        "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })
    N = len(common)

    def color(n):
        return HIGHLIGHT if n == hl else (PROPOSED if reg[n]["role"] == "proposed" else COMPARATOR)

    def save(fig, name):
        fig.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(fig_dir / f"{name}.{ext}", bbox_inches="tight", dpi=220)
        plt.close(fig)

    jf = {n: sum(truthy(r["joint_feasible"]) for r in R[n]) for n in algos}

    # 1. headline: joint feasibility, sorted horizontal bars, direct labels
    order = sorted(algos, key=lambda n: jf[n])
    fig, ax = plt.subplots(figsize=(3.5, 0.24 * len(order) + 0.7))
    ax.barh(range(len(order)), [100 * jf[n] / N for n in order], color=[color(n) for n in order],
            height=0.68, edgecolor="white", linewidth=1)
    for k, n in enumerate(order):
        ax.text(100 * jf[n] / N + 1, k, f"{jf[n]}/{N}", va="center", fontsize=7.5, color=INK)
    ax.set_yticks(range(len(order)), [lab[n] for n in order])
    ax.set_xlim(0, 112)
    ax.set_xlabel("Cases meeting deadline and budget (%)")
    ax.grid(axis="y", visible=False)
    save(fig, "joint_feasibility")

    # 2. small multiples: feasibility by dimension (dot plot, one row per algorithm)
    dims = [d for d in DIMENSIONS if d[0] in ("tasks", "qos", "family", "scenario")]
    fig, axes = plt.subplots(1, len(dims), figsize=(7.16, 0.22 * len(order) + 1.0), sharey=True)
    for ax, (key, title) in zip(axes, dims):
        vals = sorted({r[key] for r in R[algos[0]]}, key=lambda v: (ORDER.get(key, []).index(v)
                      if v in ORDER.get(key, []) else 99, int(v) if v.isdigit() else v))
        for k, n in enumerate(order):
            ys = []
            for v in vals:
                sub = [r for r in R[n] if r[key] == v]
                ys.append(100 * sum(truthy(r["joint_feasible"]) for r in sub) / len(sub))
            ax.plot(range(len(vals)), [k] * len(vals), color=GRID, lw=0.8, zorder=1)
            ax.scatter(range(len(vals)), [k] * len(vals), s=[10 + 0.9 * y for y in ys], c=color(n),
                       edgecolors="white", linewidths=0.8, zorder=2)
        ax.set_xticks(range(len(vals)), [v.replace("_constrained", "").replace("network", "net.").replace(
            "compute", "comp.") for v in vals], rotation=45, ha="right", fontsize=7)
        ax.set_title(title, loc="left")
        ax.set_xlim(-0.5, len(vals) - 0.5)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(order)), [lab[n] for n in order])
    fig.text(0.99, 0.01, "Dot area = share of cases jointly feasible", ha="right", fontsize=7, color=INK2)
    save(fig, "feasibility_by_dimension")

    # 3. feasibility vs tasks (lines) for the highlight, other proposed, and comparators
    tasks = sorted({int(r["tasks"]) for r in R[algos[0]]})
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for k, n in enumerate(sorted(algos, key=lambda n: (n != hl, reg[n]["role"] != "proposed", -jf[n]))[:8]):
        ys = []
        for t in tasks:
            sub = [r for r in R[n] if int(r["tasks"]) == t]
            ys.append(100 * sum(truthy(r["joint_feasible"]) for r in sub) / len(sub))
        ax.plot(tasks, ys, marker=MARKERS[k], ms=4.5, lw=2 if n == hl else 1.2, color=LINE_COLORS[k],
                label=lab[n], zorder=3 if n == hl else 2)
    ax.set_xscale("log")
    ax.set_xticks(tasks, [str(t) for t in tasks])
    ax.minorticks_off()
    ax.set_ylim(-3, 103)
    ax.set_xlabel("Number of tasks")
    ax.set_ylabel("Jointly feasible (%)")
    ax.legend(fontsize=6.5, ncol=2, loc="lower left")
    save(fig, "feasibility_vs_tasks")

    # 4. runtime vs tasks (median policy time, log-log)
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for k, n in enumerate(sorted(algos, key=lambda n: (n != hl, reg[n]["role"] != "proposed", -jf[n]))[:8]):
        ys = [statistics.median(int(r["runtime_ns"]) / 1e6 for r in R[n] if int(r["tasks"]) == t) for t in tasks]
        ax.plot(tasks, ys, marker=MARKERS[k], ms=4.5, lw=2 if n == hl else 1.2, color=LINE_COLORS[k], label=lab[n])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(tasks, [str(t) for t in tasks])
    ax.minorticks_off()
    ax.set_xlabel("Number of tasks")
    ax.set_ylabel("Median scheduling time (ms)")
    ax.legend(fontsize=6.5, ncol=2, loc="upper left")
    save(fig, "runtime_vs_tasks")

    # 5. paired runtime ratio vs baseline (ECDF) for proposed algorithms
    if base:
        fig, ax = plt.subplots(figsize=(3.5, 2.4))
        props = [n for n in algos if reg[n]["role"] == "proposed" and n != base]
        for k, n in enumerate(sorted(props, key=lambda n: n != hl)):
            rr = sorted(int(by[(n, i)]["runtime_ns"]) / int(by[(base, i)]["runtime_ns"]) for i in common)
            ax.step(rr, [(j + 1) / len(rr) * 100 for j in range(len(rr))], where="post",
                    lw=2 if n == hl else 1.2, color=LINE_COLORS[k], label=lab[n])
        ax.axvline(1, color=INK2, lw=0.8, ls="--")
        ax.set_xscale("log")
        ax.set_xlabel(f"Scheduling time relative to {lab[base]} (same case, same machine)")
        ax.set_ylabel("Cases (%)")
        ax.legend(fontsize=6.5, loc="lower right")
        save(fig, "runtime_ratio_ecdf")

    # 6. gains / losses of the highlight against every other algorithm (diverging bars)
    if hl:
        others = [n for n in algos if n != hl]
        g = {n: sum(truthy(by[(hl, i)]["joint_feasible"]) and not truthy(by[(n, i)]["joint_feasible"]) for i in common) for n in others}
        l = {n: sum(truthy(by[(n, i)]["joint_feasible"]) and not truthy(by[(hl, i)]["joint_feasible"]) for i in common) for n in others}
        others.sort(key=lambda n: g[n] - l[n])
        fig, ax = plt.subplots(figsize=(3.5, 0.24 * len(others) + 0.8))
        ax.barh(range(len(others)), [g[n] for n in others], color=GAIN, height=0.62, label=f"only {lab[hl]} feasible")
        ax.barh(range(len(others)), [-l[n] for n in others], color=LOSS, height=0.62, label="only the other feasible")
        lim = max([g[n] for n in others] + [l[n] for n in others] + [1]) * 1.25
        for k, n in enumerate(others):
            ax.text(g[n] + lim * 0.02, k, str(g[n]), va="center", fontsize=7)
            ax.text(-l[n] - lim * 0.02, k, str(l[n]), va="center", ha="right", fontsize=7)
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_yticks(range(len(others)), [lab[n] for n in others])
        ax.set_xlim(-lim, lim)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{abs(v):g}"))
        ax.set_xlabel("Cases")
        ax.grid(axis="y", visible=False)
        ax.legend(fontsize=6.5, loc="lower right", bbox_to_anchor=(1, 1), ncol=2)
        save(fig, "gains_losses")


if __name__ == "__main__":
    raise SystemExit(main())
