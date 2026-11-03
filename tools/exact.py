#!/usr/bin/env python3
"""RUN-BRANCH DISPATCHER for the DCR-Min v2 study. Lives on the `dcr-min-run` branch only; never merge it.

The "Exact check" workflow (.github/workflows/exact.yml) runs `tools/exact.py run ... --shard K --shards S` on
20 parallel machines with OR-tools installed and the dev + expansion data fetched. On this branch that entry
point is replaced so the same 20 machines run the DCR-Min v2 minimisation study instead:

  1. tools/minimise_v2.py run   (study shard K of S, all cores)
  2. tools/exact_min.py run     (CP-SAT optimality-gap shard K of S)
  3. push both shard CSVs to the `dcr-min-results` branch (rebase-and-retry), and once all S shards are
     there, merge them and write results/minimise_v2/summary.md on that branch
  4. exit with status 3 ON PURPOSE: a failed run job makes GitHub skip exact.yml's merge job, which would
     otherwise reset to main and commit there. Nothing is ever pushed to main.

Sizes come from tools/minimise_run.json. The real tools/exact.py is on main and on the dcr-min branch.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_BRANCH = "dcr-min-results"
OUT = Path("/tmp/minimise-out")


def sh(*cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT, check=check, text=True)


def publish(shard: int, shards: int, files: list[Path], label: str) -> None:
    sh("git", "config", "user.name", "github-actions[bot]")
    sh("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    for attempt in range(1, 11):
        sh("git", "fetch", "-q", "origin", RESULTS_BRANCH)
        sh("git", "checkout", "-q", "-f", "-B", "results", "FETCH_HEAD")
        dest = ROOT / "results" / "minimise_v2" / "shards"
        dest.mkdir(parents=True, exist_ok=True)
        for f in files:
            if f.exists():
                shutil.copy(f, dest / f.name)
        n_s, n_x = len(list(dest.glob("s-*.csv"))), len(list(dest.glob("x-*.csv")))
        if n_s == shards and n_x == shards:  # last shard in: merge and report on the results branch
            r = ROOT / "results" / "minimise_v2"
            sh(sys.executable, "tools/minimise_v2.py", "merge", "--inputs", str(dest / "s-*.csv"), "--out", str(r / "runs.csv"))
            sh(sys.executable, "tools/exact_min.py", "merge", "--inputs", str(dest / "x-*.csv"), "--out", str(r / "exact.csv"))
            sh(sys.executable, "tools/minimise_v2.py", "report", "--runs", str(r / "runs.csv"), "--exact", str(r / "exact.csv"),
               "--out", str(r / "summary.md"))
        sh("git", "add", "results/minimise_v2")
        if sh("git", "commit", "-q", "-m", f"DCR-Min v2 study: shard {shard} {label} ({n_s}/{shards} study, {n_x}/{shards} exact)",
              check=False).returncode != 0:
            return
        if sh("git", "push", "-q", "origin", f"results:{RESULTS_BRANCH}", check=False).returncode == 0:
            return
        time.sleep(3 * attempt + shard % 7)
    raise SystemExit("could not push results")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("cmd")
    p.add_argument("--data-dev")
    p.add_argument("--data-expansion")
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--shards", type=int, default=1)
    p.add_argument("--out")
    a = p.parse_args()
    if a.cmd != "run":
        raise SystemExit("run-branch dispatcher: only `run` is supported")
    c = json.loads((ROOT / "tools" / "minimise_run.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    s_out, x_out = OUT / f"s-{a.shard}.csv", OUT / f"x-{a.shard}.csv"
    study = sh(sys.executable, "tools/minimise_v2.py", "run", "--sets", "dev,expansion", "--data", "data",
               "--shard", str(a.shard), "--shards", str(a.shards), "--workers", "0", "--limit", str(c["limit"]),
               "--out", str(s_out), check=False)
    print(f"study exit {study.returncode}", flush=True)
    exact = sh(sys.executable, "tools/exact_min.py", "run", "--data", "data", "--shard", str(a.shard), "--shards", str(a.shards),
               "--time-limit", str(c["time_limit"]), "--limit", str(c["exact_limit"]), "--out", str(x_out), check=False)
    print(f"exact exit {exact.returncode}", flush=True)
    publish(a.shard, a.shards, [s_out, x_out], "study+exact")
    print("\nResults are on the dcr-min-results branch. Exiting with status 3 ON PURPOSE so that exact.yml's "
          "merge job (which commits to main) is skipped.", flush=True)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
