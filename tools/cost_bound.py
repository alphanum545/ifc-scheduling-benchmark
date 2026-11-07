#!/usr/bin/env python3
"""Lagrangian cost lower bound for deadline-constrained cost minimization (paper 2, DCR-Cost).

For a QoS instance, the bound relaxes the per-resource capacity constraints at DCR's four checkpoints
theta_k in {D/4, D/2, 3D/4, D}:
  g_jrk = max(0, p_jr - max(0, b_j - theta_k))   mandatory work of j on r before theta_k
  A_j   = DCR's deadline-feasible domain of j at step 0 (necessary, optimistic conditions)
  L(z)  = sum_j min_{r in A_j} (c_jr + sum_k z_rk g_jrk) - sum_{r,k} z_rk theta_k  <=  C*   for any z >= 0.
Prices are searched with a Polyak-step subgradient method in floating point; the best prices are then
re-evaluated in exact rational arithmetic, so the returned bound is exact and valid.

Reported per instance:
  C_min   sum_j min_r c_jr (deadline ignored)
  LB_dom  L(0): cheapest cost over deadline-feasible domains
  LB_3    DCR v1's own three-price-vector reserve at step 0 (pool.current / H)
  LB_sg   best exact L(z) from the extended search
  LB_best ceil(max(LB_dom, LB_3, LB_sg))
  C_ref   the dataset's deadline-conditioned reference cost (budget.cost_floor_ref_ncu)

  python3 tools/cost_bound.py --data data/dev --out results/bounds/bounds-dev.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

SG_ITERS = 400
FIELDS = ["set", "instance_id", "family", "qos", "tasks", "resources", "deadline_us",
          "C_min", "LB_dom", "LB_3", "LB_sg", "LB_best", "C_ref"]


def _arrays(inp):
    import numpy as np
    from algorithms.dcr_ifc.model import Model
    from algorithms.dcr_ifc_optimized.state import State
    md = Model.create(inp)
    st = State(md)
    c = np.array(md.c, dtype=np.int64)
    g = np.array(md.g, dtype=np.int64)
    K = np.array(st.K, dtype=np.int64)
    mask = np.array(st.active, dtype=bool)
    return md, st, c, g, K, mask


def lagrangian_exact(c, g, K, mask, z) -> Fraction:
    zf = [[Fraction(v) for v in row] for row in z]
    n, m, k = g.shape
    total = Fraction(0)
    for j in range(n):
        best = None
        for r in range(m):
            if mask[j, r]:
                w = Fraction(int(c[j, r])) + sum(zf[r][t] * int(g[j, r, t]) for t in range(k) if g[j, r, t])
                best = w if best is None or w < best else best
        total += best
    return total - sum(zf[r][t] * int(K[r, t]) for r in range(m) for t in range(k))


def subgradient(c, g, K, mask, target: float, iters: int = SG_ITERS):
    import numpy as np
    n, m, k = g.shape
    cf, gf, Kf = c.astype(float), g.astype(float), K.astype(float)
    big = np.where(mask, 0.0, np.inf)
    z = np.zeros((m, k))
    best_val, best_z, lam, stall = -np.inf, z.copy(), 2.0, 0
    rows = np.arange(n)
    for _ in range(iters):
        W = cf + np.einsum("jrk,rk->jr", gf, z) + big
        arg = W.argmin(1)
        val = W[rows, arg].sum() - (z * Kf).sum()
        if val > best_val + 1e-9 * max(1.0, abs(val)):
            best_val, best_z, stall = val, z.copy(), 0
        else:
            stall += 1
            if stall >= 20:
                lam, stall = lam / 2, 0
                if lam < 1e-4:
                    break
        demand = np.zeros((m, k))
        np.add.at(demand, arg, gf[rows, arg])
        s = demand - Kf
        nrm = (s * s).sum()
        if nrm == 0:
            break
        z = np.maximum(0.0, z + lam * max(target - val, 1e-9 * max(1.0, target)) / nrm * s)
    return best_z


def bounds(inp, c_ref: int) -> dict:
    import numpy as np
    from algorithms.dcr_ifc_v1.reserve import ReservePool
    md, st, c, g, K, mask = _arrays(inp)
    lb_dom = int(np.where(mask, c, np.iinfo(np.int64).max).min(1).sum())
    pool = ReservePool(st)
    pool.refresh_minima(st)
    lb3 = Fraction(pool.current, md.H)
    z = subgradient(c, g, K, mask, float(c_ref) if c_ref else 2.0 * lb_dom + 1)
    lb_sg = lagrangian_exact(c, g, K, mask, z.tolist())
    return {"tasks": len(md.tasks), "resources": len(md.resources), "deadline_us": md.D,
            "C_min": int(sum(md.cmin)), "LB_dom": lb_dom, "LB_3": math.ceil(lb3), "LB_sg": math.ceil(lb_sg),
            "LB_best": math.ceil(max(Fraction(lb_dom), lb3, lb_sg))}


def load_input(base: dict, qos: dict):
    from algorithms.common.interface import AlgorithmInput
    return AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split="development")


def main() -> int:
    import bench
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--set", default="dev")
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    man = bench.manifest(a.set)
    bases = {b["base_instance_id"]: b for b in man["base_entries"]}
    root, out = Path(a.data), Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for e in man["entries"]:
            base = json.loads((root / bases[e["base_instance_id"]]["path"]).read_text())
            qos = json.loads((root / e["path"]).read_text())
            c_ref = int(qos["budget"]["cost_floor_ref_ncu"])
            row = {"set": a.set, "instance_id": e["instance_id"], "family": e["family"], "qos": e["qos_profile"],
                   "C_ref": c_ref, **bounds(load_input(base, qos), c_ref)}
            w.writerow(row)
            fh.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
