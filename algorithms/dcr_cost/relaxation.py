"""Shared Lagrangian relaxation pieces for DCR-Cost (paper 2): chain cuts on top of the capacity relaxation."""
from __future__ import annotations

SG_ITERS = 400
MAX_PATHS = 64


def _longest_path(order, parents, dur):
    """Longest path (sum of task durations, communication taken as 0) in a DAG; returns (length, tasks)."""
    best, pred = {}, {}
    for j in order:
        b, pj = 0.0, None
        for q in parents[j]:
            if best[q] > b:
                b, pj = best[q], q
        best[j], pred[j] = b + dur[j], pj
    end = max(best, key=lambda j: best[j])
    path, j = [], end
    while j is not None:
        path.append(j)
        j = pred[j]
    return best[end], path[::-1]


def subgradient_chain(c, g, K, mask, p, order, parents, D, target: float, iters: int = SG_ITERS,
                      max_paths: int = MAX_PATHS):
    """Capacity + chain relaxation. A chain P of the DAG runs sequentially, so every schedule meeting D has
    sum_{j in P} p_{j,x(j)} <= D (communication >= 0 is dropped). Violated chains under the current
    Lagrangian assignment are added on the fly (cutting planes) with multipliers mu_P >= 0."""
    import numpy as np
    n, m, k = g.shape
    cf, gf, Kf, pf = c.astype(float), g.astype(float), K.astype(float), p.astype(float)
    big = np.where(mask, 0.0, np.inf)
    rows = np.arange(n)
    z = np.zeros((m, k))
    paths, seen, mu = [], set(), np.zeros(0)
    best = (-np.inf, z.copy(), [], np.zeros(0))
    lam, stall = 2.0, 0
    for _ in range(iters):
        coef = np.zeros(n)
        for P, u in zip(paths, mu):
            if u:
                coef[P] += u
        W = cf + np.einsum("jrk,rk->jr", gf, z) + coef[:, None] * pf + big
        arg = W.argmin(1)
        val = W[rows, arg].sum() - (z * Kf).sum() - D * mu.sum()
        if val > best[0] + 1e-9 * max(1.0, abs(val)):
            best, stall = (val, z.copy(), list(paths), mu.copy()), 0
        else:
            stall += 1
            if stall >= 20:
                lam, stall = lam / 2, 0
                if lam < 1e-4:
                    break
        dur = pf[rows, arg]
        if len(paths) < max_paths:
            length, path = _longest_path(order, parents, dur)
            key = tuple(path)
            if length > D and key not in seen:
                seen.add(key)
                paths.append(np.array(path))
                mu = np.append(mu, 0.0)
        demand = np.zeros((m, k))
        np.add.at(demand, arg, gf[rows, arg])
        s_cap = demand - Kf
        s_path = np.array([dur[P].sum() - D for P in paths])
        nrm = (s_cap * s_cap).sum() + (s_path * s_path).sum()
        if nrm == 0:
            break
        step = lam * max(target - val, 1e-9 * max(1.0, target)) / nrm
        z = np.maximum(0.0, z + step * s_cap)
        mu = np.maximum(0.0, mu + step * s_path)
    return best[1], best[2], best[3]
