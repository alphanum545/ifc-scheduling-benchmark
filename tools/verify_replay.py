#!/usr/bin/env python3
"""Check that runs in results/store.csv reproduce the historical results exactly.

The historical results were produced before this repository existed (AWS Lambda,
ap-south-2, Python 3.11, September-October 2026) by the same algorithm source files.
They are kept under reference/:

  primary-1120.jsonl  the 160-case x 7-comparator development experiment
  dcr-stored.json     per-instance DCR results (Stage15/16 symmetric runs, the DCR-v0
                      development run, and the 15 Oct 2026 24-case DCR-v1/v3 reproduction)

For every store row whose algorithm names a reference, each outcome field present in the
reference is compared for exact equality. Runtimes are environment-dependent and are not
compared.

  python3 tools/verify_replay.py [--out results/replay.md] [--strict]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import ROOT, read_store, registry  # noqa: E402

FIELDS = {  # store field -> reference field
    "schedule_id": "schedule_id",
    "schedule_sha256": "schedule_sha256",
    "makespan_us": "makespan_us",
    "compute_cost_ncu": "compute_cost_ncu",
    "compute_energy_nj": "compute_energy_nj",
    "network_energy_pj": "network_energy_pj",
    "joint_feasible": "joint_feasible",
    "deadline_met": ("deadline_met", "deadline_feasible"),
    "budget_met": ("budget_met", "budget_feasible"),
}


def load_references() -> dict[str, dict[str, dict]]:
    refs: dict[str, dict[str, dict]] = defaultdict(dict)
    for line in open(ROOT / "reference" / "primary-1120.jsonl", encoding="utf-8"):
        r = json.loads(line)
        refs[f"primary:{r['algorithm_id']}"][r["instance_id"]] = r
    for key, rows in json.load(open(ROOT / "reference" / "dcr-stored.json", encoding="utf-8")).items():
        name, _, tag = key.partition("@")
        prefix = "core24" if tag == "core24" else "dcr"
        refs[f"{prefix}:{name}{'@' + tag if tag and tag != 'core24' else ''}"].update(rows)
    return refs


def norm(v):
    if isinstance(v, bool):
        return v
    s = str(v).strip()
    if s in ("True", "False"):
        return s == "True"
    try:
        return int(s)
    except ValueError:
        return s


def compare(row: dict, ref: dict) -> list[str]:
    diffs = []
    for mine, theirs in FIELDS.items():
        names = theirs if isinstance(theirs, tuple) else (theirs,)
        name = next((n for n in names if n in ref and ref[n] is not None), None)
        if name is None or row.get(mine) in (None, ""):
            continue
        if norm(row[mine]) != norm(ref[name]):
            diffs.append(f"{mine}: {row[mine]} != {ref[name]}")
    return diffs


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default=str(ROOT / "results" / "replay.md"))
    p.add_argument("--strict", action="store_true", help="exit 1 on any mismatch")
    a = p.parse_args()
    reg = registry()
    refs = load_references()
    rows = [r for r in read_store() if r["status"] == "ok" and r["algo"] in reg
            and r["source_sha256"] == reg[r["algo"]]["source_sha256"]]
    lines = ["# Replay against historical results", "",
             "Each run in `results/store.csv` made with the current source is compared field by field with the stored",
             "historical result for the same algorithm version and instance (schedule identity, makespan, cost, energy,",
             "feasibility). Runtimes are not compared.", "",
             "| Algorithm | Reference set | Instances compared | Exact matches | Mismatches |",
             "| --- | --- | ---: | ---: | ---: |"]
    total_bad = 0
    details = []
    for name, spec in reg.items():
        targets = spec.get("reference", [])
        targets = [targets] if isinstance(targets, str) else targets
        mine = [r for r in rows if r["algo"] == name]
        for t in targets:
            ref = refs.get(t, {})
            compared = [(r, ref[r["instance_id"]]) for r in mine if r["instance_id"] in ref]
            if not compared:
                continue
            bad = [(r["instance_id"], d) for r, x in compared if (d := compare(r, x))]
            total_bad += len(bad)
            lines.append(f"| {spec['label']} | `{t}` | {len(compared)} | {len(compared) - len(bad)} | {len(bad)} |")
            details += [f"- {spec['label']} `{t}` {iid}: {'; '.join(d)}" for iid, d in bad[:10]]
    lines += ["", f"**Total mismatches: {total_bad}.**" + ("" if total_bad else " Every compared run reproduces its historical result exactly.")]
    if details:
        lines += ["", "## First mismatches", ""] + details
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 1 if (a.strict and total_bad) else 0


if __name__ == "__main__":
    raise SystemExit(main())
