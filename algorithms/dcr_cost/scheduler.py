"""DCR-Cost: deadline-constrained cost minimization with a Lagrangian cost-bound ranking (paper 2).

Problem: minimize total compute cost subject to the deadline D. There is no budget; the
scheduler ignores budget_ncu entirely.

Reused from DCR-v1 (companion paper): earliest-start / latest-finish windows, active domains,
insertion calendars, capacity deletions, the exact child-arrival correction, task priority,
price epochs and the permanent earliest-finish fallback.

New here:
  * Prices. At every price epoch the three price vectors are (0, z, z/2), where z comes from a
    Polyak subgradient search on the Lagrangian capacity relaxation of the REMAINING tasks
    (tools/cost_bound.py at step 0). DCR's budget-scaled updates are not used.
  * Ranking. Among placements that pass the time screens, choose the smallest
        G+(i, r) = H*(cost already spent + c_ir) + lower bound on the cost of all remaining tasks
    after the placement (with capacity deletions and child-arrival restrictions), ties by
    (finish, cost, resource). This is an A*-style greedy: cost so far plus an admissible estimate.
  * rank = "cheapest" is the predeclared ablation: rank by c_ir only (same screens).

Deterministic; no tuned parameters (subgradient: SG_ITERS = 200 iterations per price epoch, the same
Polyak step rule as tools/cost_bound.py with a loose upper estimate as target).
"""
from __future__ import annotations

import dataclasses
import math
from fractions import Fraction
from hashlib import sha256

from generator.canonical import canonical_json_bytes
from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from algorithms.dcr_ifc.model import Model
from algorithms.dcr_ifc.reserve import dot
from algorithms.dcr_ifc.state import MonotoneChoices
from algorithms.dcr_ifc_optimized.state import State
from algorithms.dcr_ifc_v1.reserve import ReservePool

DESIGN_VERSION = "dcr_cost_design_20261108"
SG_ITERS = 200


def _subgradient_prices(state, iters: int = SG_ITERS):
    """Float prices z >= 0 (cost units) for the remaining tasks' capacity relaxation."""
    import numpy as np
    md = state.model
    U = list(state.U)
    m, k = len(md.resources), len(md.theta)
    c = np.array([md.c[j] for j in U], dtype=float)
    g = np.array([md.g[j] for j in U], dtype=float)
    mask = np.array([state.active[j] for j in U], dtype=bool)
    K = np.array(state.K, dtype=float)
    big = np.where(mask, 0.0, np.inf)
    target = float(np.where(mask, c, -np.inf).max(1).sum()) + 1.0  # loose upper estimate
    z = np.zeros((m, k))
    best_val, best_z, lam, stall = -np.inf, z.copy(), 2.0, 0
    rows = np.arange(len(U))
    for _ in range(iters):
        W = c + np.einsum("jrk,rk->jr", g, z) + big
        arg = W.argmin(1)
        val = W[rows, arg].sum() - (z * K).sum()
        if val > best_val + 1e-9 * max(1.0, abs(val)):
            best_val, best_z, stall = val, z.copy(), 0
        else:
            stall += 1
            if stall >= 20:
                lam, stall = lam / 2, 0
                if lam < 1e-4:
                    break
        demand = np.zeros((m, k))
        np.add.at(demand, arg, g[rows, arg])
        s = demand - K
        nrm = (s * s).sum()
        if nrm == 0:
            break
        z = np.maximum(0.0, z + lam * max(target - val, 1e-9 * max(1.0, target)) / nrm * s)
    return best_z


class CostPool(ReservePool):
    """DCR-v1 reserve machinery with subgradient prices (0, z, z/2) instead of budget-scaled ones."""

    def __init__(self, state) -> None:  # noqa: D401 - replaces the parent constructor
        md = state.model
        m, k = len(md.resources), len(md.theta)
        zf = _subgradient_prices(state)
        Z1 = [[int(round(md.H * zf[r][t])) for t in range(k)] for r in range(m)]
        Z2 = [[v // 2 for v in row] for row in Z1]
        self.prices = [[[0] * k for _ in range(m)], Z1, Z2]
        self.weights, self.choices = [], []
        for z in self.prices:
            weights = {j: [md.H * md.c[j][r] + dot(z[r], md.g[j][r]) for r in range(m)] for j in state.U}
            orders = {j: sorted((r for r in range(m) if state.active[j][r]),
                                key=lambda r: (weights[j][r], md.p[j][r], r)) for j in state.U}
            if any(not o for o in orders.values()):
                raise ValueError("cannot price an empty resource domain")
            self.weights.append(weights)
            self.choices.append({j: MonotoneChoices(o) for j, o in orders.items()})
        self.minimum, self.totals, self.current = [], [], 0
        self._order_size, self._spent, self._capacity = None, 0, []


class DCRCostScheduler:
    algorithm_id = "dcr_cost_bound"
    algorithm_version = "dcr_cost_bound_design_20261108_impl1"
    rank = "bound"  # bound | cheapest

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR-Cost is deterministic and accepts seed=None only")
        return self._schedule_with(scheduling_input, Fraction(1))

    def _schedule_with(self, scheduling_input: AlgorithmInput, gamma: Fraction) -> AlgorithmDecision:
        md = _with_tail_inflation(Model.create(scheduling_input), gamma)
        st = State(md)
        m = len(md.resources)
        stats: dict[str, object] = {"design_version": DESIGN_VERSION, "rank": self.rank, "gamma": str(gamma), "price_refresh_count": 0,
                                    "first_fallback_step": None, "first_fallback_reason": None,
                                    "fallback_task_count": 0, "screened_candidate_count": 0}
        pool = None
        fallback = False
        while st.U:
            i = st.choose_task()
            placements = [st.insertion(i, r) for r in range(m)]
            screened, reason = [], "empty_screen"
            if not fallback:
                if any(st.count[j] == 0 for j in st.U):
                    reason = "empty_current_domain"
                elif md.b[i] - min(f for _, f in placements) < 0:
                    reason = "negative_time_margin"
                else:
                    if len(st.order) in md.epochs or pool is None:
                        pool = CostPool(st)
                        stats["price_refresh_count"] += 1
                    pool.refresh_minima(st)
                    candidates = {}
                    for r in range(m):
                        s, f = placements[r]
                        if not st.active[i][r] or f > md.b[i]:
                            continue
                        deleted = st.capacity_deletions(i, r, s, f)
                        if deleted is not None:
                            candidates[r] = deleted
                    pool.prepare(st, i, placements, candidates)
                    for r, deleted in candidates.items():
                        s, f = placements[r]
                        bounds = pool.candidate_bounds(st, i, r, s, f, deleted)
                        if bounds is None:
                            continue
                        key = (bounds[1], f, md.c[i][r], r) if self.rank == "bound" else (md.c[i][r], f, r)
                        screened.append((key, r))
                    stats["screened_candidate_count"] += len(screened)
            if screened:
                r = min(screened)[1]
            else:
                r = min(range(m), key=lambda q: (placements[q][1], md.c[i][q], q))
                if not fallback:
                    stats["first_fallback_step"] = len(st.order) + 1
                    stats["first_fallback_reason"] = reason
                fallback = True
                stats["fallback_task_count"] += 1
            s, f = placements[r]
            st.commit(i, r, s, f)
        assignments = [{"task_id": md.tasks[i], "resource_id": md.resources[st.placements[i][0]],
                        "start_us": st.placements[i][1], "end_us": st.placements[i][2]} for i in range(len(md.tasks))]
        stats["planned_assignments_sha256"] = sha256(canonical_json_bytes(assignments)).hexdigest()
        stats["internal_makespan_us"] = max(f for _, _, f in st.placements.values())
        stats["internal_compute_cost_ncu"] = st.spent
        return AlgorithmDecision(tuple(md.tasks[i] for i in st.order),
                                 {md.tasks[i]: md.resources[r] for i, (r, _, _) in st.placements.items()}, stats)


def _with_tail_inflation(md: Model, gamma: Fraction) -> Model:
    """Same instance, latest finishes tightened to b_i = D - ceil(gamma * h_i) (gamma = 1 is DCR's b)."""
    if gamma == 1:
        return md
    n, m = len(md.tasks), len(md.resources)
    b = tuple(md.D - math.ceil(gamma * md.h[i]) for i in range(n))
    g = tuple(tuple(tuple(max(0, md.p[i][r] - max(0, b[i] - t)) for t in md.theta) for r in range(m)) for i in range(n))
    return dataclasses.replace(md, b=b, sigma=tuple(b[i] - md.pmin[i] for i in range(n)), g=g)


class DCRCostPortfolioScheduler(DCRCostScheduler):
    """Step 2: run the bound rule with tail-inflation factors gamma in GRID (predeclared, the same grid as
    DCR-v3's pacing members) and return the cheapest plan whose own calendar meets D. If none does, return
    the deadline guardrail: DCR-v1 Admission with an unbinding budget (its deadline screens only)."""
    algorithm_id = "dcr_cost_portfolio"
    algorithm_version = "dcr_cost_portfolio_design_20261108_impl1"
    GRID = (Fraction(1), Fraction(5, 4), Fraction(3, 2), Fraction(2), Fraction(3))

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR-Cost is deterministic and accepts seed=None only")
        D = scheduling_input.deadline_us
        best, tried = None, []
        for gamma in self.GRID:
            d = self._run(scheduling_input, gamma)
            s = d.internal_statistics
            ok = s["internal_makespan_us"] <= D
            tried.append((str(gamma), ok, s["internal_compute_cost_ncu"]))
            if ok and (best is None or s["internal_compute_cost_ncu"] < best[1].internal_statistics["internal_compute_cost_ncu"]):
                best = (gamma, d)
        if best is None:
            from algorithms.dcr_ifc_v1.scheduler import DCRV1AdmissionScheduler
            inst = scheduling_input.instance
            unbinding = sum(max(int(v) for v in row.values()) for row in inst["compute_cost_ncu"].values())
            guard_input = dataclasses.replace(scheduling_input, budget_ncu=unbinding)
            d = DCRV1AdmissionScheduler().schedule(guard_input)
            stats = dict(d.internal_statistics, portfolio=tried, chosen="guardrail_dcr_v1_admission")
            return AlgorithmDecision(d.task_order, d.resource_assignments, stats)
        gamma, d = best
        return AlgorithmDecision(d.task_order, d.resource_assignments,
                                 dict(d.internal_statistics, portfolio=tried, chosen=str(gamma)))

    def _run(self, scheduling_input, gamma):
        return DCRCostScheduler._schedule_with(self, scheduling_input, gamma)


class DCRCostCheapestScheduler(DCRCostScheduler):
    """Ablation: same screens, rank by the placement's own cost only."""
    algorithm_id = "dcr_cost_cheapest"
    algorithm_version = "dcr_cost_cheapest_design_20261108_impl1"
    rank = "cheapest"
