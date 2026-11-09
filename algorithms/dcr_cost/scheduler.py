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
from algorithms.dcr_ifc.model import Model, overlap
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


class ChainCostPool(CostPool):
    """Capacity + chain prices. A chain P of the DAG runs sequentially, so sum_{j in P} p_{j,x(j)} <= D.
    Violated chains are generated on the fly (algorithms/dcr_cost/relaxation.py). Committed tasks are fixed
    to their resource (cost 0, capacity already deducted from K), so their chain durations count as constants.

    Price vector l has chain coefficients coef_l[j] (sum of mu_P over chains P containing j; 0, mu, mu/2).
    Remaining-task weights gain H*coef_l[j]*p_jr; the constant  H*sum_{committed j} coef_l[j]*p_j - H*D*sum mu_l
    is kept separately and added to every total and candidate bound, so each vector stays a valid bound."""

    def __init__(self, state) -> None:
        import numpy as np
        from .relaxation import subgradient_chain

        md = state.model
        n, m, k = len(md.tasks), len(md.resources), len(md.theta)
        c = np.array(md.c, dtype=np.int64)
        g = np.array(md.g, dtype=np.int64)
        mask = np.array(state.active, dtype=bool)
        for j, (r, _, _) in state.placements.items():
            c[j, :] = 0
            g[j, :, :] = 0
            mask[j, :] = False
            mask[j, r] = True
        p = np.array(md.p, dtype=np.int64)
        target = float(np.where(mask, c, -1).max(1).sum()) + 1.0
        zf, paths, mu = subgradient_chain(c, g, np.array(state.K, dtype=np.int64), mask, p,
                                          list(md.topological), md.parents, md.D, target, iters=SG_ITERS)
        coef = np.zeros(n)
        for P, u in zip(paths, mu):
            coef[P] += u
        Z1 = [[int(round(md.H * zf[r][t])) for t in range(k)] for r in range(m)]
        C1 = [int(round(md.H * v)) for v in coef]
        self.prices = [[[0] * k for _ in range(m)], Z1, [[v // 2 for v in row] for row in Z1]]
        self.coef = [[0] * n, C1, [v // 2 for v in C1]]
        musum = int(round(md.H * float(mu.sum())))
        self.mu_const = [0, -md.D * musum, -md.D * (musum // 2)]
        self.weights, self.choices = [], []
        for z, cf in zip(self.prices, self.coef):
            weights = {j: [md.H * md.c[j][r] + dot(z[r], md.g[j][r]) + cf[j] * md.p[j][r] for r in range(m)]
                       for j in state.U}
            orders = {j: sorted((r for r in range(m) if state.active[j][r]),
                                key=lambda r: (weights[j][r], md.p[j][r], r)) for j in state.U}
            if any(not o for o in orders.values()):
                raise ValueError("cannot price an empty resource domain")
            self.weights.append(weights)
            self.choices.append({j: MonotoneChoices(o) for j, o in orders.items()})
        self.minimum, self.totals, self.current = [], [], 0
        self._order_size, self._spent, self._capacity = None, 0, []
        self._fixed = [sum(cf[j] * md.p[j][r] for j, (r, _, _) in state.placements.items()) for cf in self.coef]
        self._fixed_count = len(state.order)

    def _const(self, state) -> list[int]:
        md = state.model
        for j in state.order[self._fixed_count:]:
            r = state.placements[j][0]
            for ell, cf in enumerate(self.coef):
                self._fixed[ell] += cf[j] * md.p[j][r]
        self._fixed_count = len(state.order)
        return [f + mc for f, mc in zip(self._fixed, self.mu_const)]

    def refresh_minima(self, state) -> None:
        super().refresh_minima(state)
        self.adjusted = [t + k for t, k in zip(self.totals, self._const(state))]
        self.adjusted_current = max(self.adjusted)

    def candidate_bounds(self, state, i, r, start, finish, deleted):
        if r in self.empty:
            return None
        md = state.model
        occupation = tuple(overlap(start, finish, 0, theta) for theta in md.theta)
        capacity, arrival = [], []
        for ell, z in enumerate(self.prices):
            w, mins = self.weights[ell], self.minimum[ell]
            base = (self.adjusted[ell] + md.H * md.c[i][r] + self.coef[ell][i] * md.p[i][r]
                    - w[i][mins[i][0]] + dot(z[r], occupation))
            old, new = base, base + self.arrival_delta[r][ell]
            for j in deleted:
                first, second = mins[j]
                if first == r:
                    if second is None:
                        raise ArithmeticError("candidate removes the only capacity option")
                    delta = w[j][second] - w[j][first]
                    old += delta
                    if j not in self.child_set:
                        new += delta
            capacity.append(old)
            arrival.append(new)
        old, new = max(capacity), max(arrival)
        if not self.adjusted_current <= old <= new:
            raise ArithmeticError("reserve monotonicity violated")
        return old, new


class DCRCostScheduler:
    algorithm_id = "dcr_cost_bound"
    algorithm_version = "dcr_cost_bound_design_20261108_impl1"
    rank = "bound"  # bound | cheapest
    pool_class = CostPool

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
                        pool = self.pool_class(st)
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
            d = self._guardrail(scheduling_input)
            stats = dict(d.internal_statistics, portfolio=tried, chosen="guardrail_dcr_v1_admission")
            return AlgorithmDecision(d.task_order, d.resource_assignments, stats)
        gamma, d = best
        return AlgorithmDecision(d.task_order, d.resource_assignments,
                                 dict(d.internal_statistics, portfolio=tried, chosen=str(gamma)))

    def _run(self, scheduling_input, gamma):
        return DCRCostScheduler._schedule_with(self, scheduling_input, gamma)

    @staticmethod
    def _guardrail(scheduling_input):
        """DCR-v1 Admission with an unbinding budget (its deadline screens only)."""
        from algorithms.dcr_ifc_v1.scheduler import DCRV1AdmissionScheduler
        inst = scheduling_input.instance
        unbinding = sum(max(int(v) for v in row.values()) for row in inst["compute_cost_ncu"].values())
        return DCRV1AdmissionScheduler().schedule(dataclasses.replace(scheduling_input, budget_ncu=unbinding))


class _Simulator:
    """Exact replica of generator.schedule.build_schedule for a fixed task order: tasks in order, ready time
    = max over parents of (parent end + tier-route communication, 0 on the same resource), then the earliest
    idle slot on the assigned resource (insertion). Public instance data only."""

    def __init__(self, md: Model, order: list[int]) -> None:
        self.md, self.order = md, order
        self.pos = {i: k for k, i in enumerate(order)}
        tiers = sorted(set(md.tiers))
        self.tier_of = [tiers.index(t) for t in md.tiers]
        ex = {t: [r for r in range(len(md.resources)) if md.tiers[r] == t] for t in tiers}
        self.comm = {}
        for (i, j) in md.bits:
            table = [[None] * len(tiers) for _ in tiers]
            for a, ta in enumerate(tiers):
                for b, tb in enumerate(tiers):
                    src = ex[ta][0]
                    dst = next((q for q in ex[tb] if q != src), None)
                    if dst is not None:
                        table[a][b] = md.delay(i, j, src, dst)
            self.comm[i, j] = table

    def makespan(self, assign: list[int], limit: int | None = None) -> int:
        return self.run(assign, limit=limit)[0]

    def run(self, assign: list[int], k: int = 0, base: tuple | None = None, limit: int | None = None):
        """Simulate order[k:] on top of the prefix order[:k] taken from base = (end, cals) of an earlier full
        run. Tasks before position k never depend on later tasks (they are placed first), so the result equals
        a full rebuild. Returns (makespan, end, cals); with an early exit the last two are partial."""
        md = self.md
        if base is None or k == 0:
            end, cals, worst = [0] * len(assign), [[] for _ in md.resources], 0
            k = 0
        else:
            pos = self.pos
            bend, bcals = base
            end = list(bend)
            cals = [[iv for iv in cal if pos[iv[2]] < k] for cal in bcals]
            worst = max((end[self.order[j]] for j in range(k)), default=0)
        for i in self.order[k:]:
            r = assign[i]
            ready = 0
            for p in md.parents[i]:
                rp = assign[p]
                d = 0 if rp == r else self.comm[p, i][self.tier_of[rp]][self.tier_of[r]]
                if end[p] + d > ready:
                    ready = end[p] + d
            dur = md.p[i][r]
            start = ready
            cal = cals[r]
            pos_ = 0
            for pos_, (s, e, _) in enumerate(cal):
                if start + dur <= s:
                    break
                if start < e:
                    start = e
            else:
                pos_ = len(cal)
            cal.insert(pos_, (start, start + dur, i))
            end[i] = start + dur
            if end[i] > worst:
                worst = end[i]
                if limit is not None and worst > limit:
                    return worst, end, cals  # early exit: already infeasible
        return worst, end, cals


def improve(md: Model, order: list[int], assign: list[int], max_tries_per_task: int = 3,
            max_passes: int = 2) -> tuple[list[int], dict]:
    """First-improvement downgrade search: move a task to a cheaper resource if the exact rebuild still
    meets D. Tasks by largest possible saving first; per task, cheaper resources by ascending cost, at most
    max_tries_per_task rebuilds. Every accepted move keeps makespan <= D, so feasibility is preserved."""
    sim = _Simulator(md, order)
    D = md.D
    assign = list(assign)
    stats = {"improve_moves": 0, "improve_rebuilds": 0, "improve_saving_ncu": 0, "improve_passes": 0}
    ms, end, cals = sim.run(assign)
    if ms > D:
        stats["improve_skipped"] = "start_plan_misses_deadline"
        return assign, stats
    base = (end, cals)
    for _ in range(max_passes):
        stats["improve_passes"] += 1
        moved = False
        tasks = sorted(range(len(assign)), key=lambda i: (-(md.c[i][assign[i]] - md.cmin[i]), i))
        for i in tasks:
            cur = assign[i]
            options = sorted((q for q in range(len(md.resources)) if md.c[i][q] < md.c[i][cur]),
                             key=lambda q: (md.c[i][q], md.p[i][q], q))[:max_tries_per_task]
            for q in options:
                assign[i] = q
                stats["improve_rebuilds"] += 1
                if sim.run(assign, k=sim.pos[i], base=base, limit=D)[0] <= D:
                    base = sim.run(assign)[1:]  # new prefix source after an accepted move
                    stats["improve_moves"] += 1
                    stats["improve_saving_ncu"] += md.c[i][cur] - md.c[i][q]
                    moved = True
                    break
                assign[i] = cur
        if not moved:
            break
    return assign, stats


class DCRCostImprovedScheduler(DCRCostPortfolioScheduler):
    """Step 3: the portfolio plan followed by the downgrade improvement pass (same task order)."""
    algorithm_id = "dcr_cost_improved"
    algorithm_version = "dcr_cost_improved_design_20261108_impl1"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        d = super().schedule(scheduling_input, seed=seed)
        md = Model.create(scheduling_input)
        idx_t = {t: i for i, t in enumerate(md.tasks)}
        idx_r = {r: q for q, r in enumerate(md.resources)}
        order = [idx_t[t] for t in d.task_order]
        assign = [0] * len(md.tasks)
        for t, r in d.resource_assignments.items():
            assign[idx_t[t]] = idx_r[r]
        new, st = improve(md, order, assign)
        mapping = {md.tasks[i]: md.resources[new[i]] for i in range(len(md.tasks))}
        stats = dict(d.internal_statistics, **st)
        stats["internal_compute_cost_ncu"] = sum(md.c[i][new[i]] for i in range(len(md.tasks)))
        return AlgorithmDecision(d.task_order, mapping, stats)


class DCRCostChainImprovedScheduler(DCRCostImprovedScheduler):
    """Portfolio + improvement, with capacity + chain prices in the ranking bound."""
    algorithm_id = "dcr_cost_chain_improved"
    algorithm_version = "dcr_cost_chain_improved_design_20261108_impl1"
    pool_class = ChainCostPool


class DCRCostCheapestScheduler(DCRCostScheduler):
    """Ablation: same screens, rank by the placement's own cost only."""
    algorithm_id = "dcr_cost_cheapest"
    algorithm_version = "dcr_cost_cheapest_design_20261108_impl1"
    rank = "cheapest"


class DCRCostSplitScheduler(DCRCostPortfolioScheduler):
    """Step 4 (DCR-Cost v2): a wider candidate set, every feasible candidate improved.

    Candidates: the bound-rule plans for every gamma in GRID; the DCR-v1 Admission guardrail when none of
    them meets D by its own calendar (exactly when v1 returns the guardrail); and the deterministic
    deadline-distribution plans for every lambda in split.SPLIT_GRID. So v2's candidates include v1's, and
    v2 never costs more than v1. Each candidate whose exact rebuild meets D goes through the downgrade
    improvement pass, and the cheapest improved plan is returned (ties: candidate order above). If no
    candidate meets D, the guardrail is returned unimproved."""
    algorithm_id = "dcr_cost_split"
    algorithm_version = "dcr_cost_split_design_20261109_impl1"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        from .split import SPLIT_GRID, deadline_split
        if seed is not None:
            raise AlgorithmContractError("DCR-Cost is deterministic and accepts seed=None only")
        D = scheduling_input.deadline_us
        md = Model.create(scheduling_input)
        idx_t = {t: i for i, t in enumerate(md.tasks)}
        idx_r = {r: q for q, r in enumerate(md.resources)}
        cands = []
        any_bound_ok = False
        for gamma in self.GRID:
            d = self._run(scheduling_input, gamma)
            any_bound_ok |= d.internal_statistics["internal_makespan_us"] <= D
            cands.append((f"gamma={gamma}", list(d.task_order), dict(d.resource_assignments)))
        guard = None
        if not any_bound_ok:  # exactly when DCR-Cost v1 returns its guardrail: keep it as a candidate
            guard = self._guardrail(scheduling_input)
            cands.append(("guardrail_dcr_v1_admission", list(guard.task_order), dict(guard.resource_assignments)))
        for lam in SPLIT_GRID:
            order, mapping, _, _ = deadline_split(scheduling_input.instance, D, lam)
            cands.append((f"split_lambda={lam}", order, mapping))
        tried, best = [], None
        for name, order_t, mapping in cands:
            order = [idx_t[t] for t in order_t]
            assign = [idx_r[mapping[md.tasks[i]]] for i in range(len(md.tasks))]
            if _Simulator(md, order).makespan(assign) > D:
                tried.append((name, False, None))
                continue
            new, st = improve(md, order, assign)
            c = sum(md.c[i][new[i]] for i in range(len(new)))
            tried.append((name, True, c))
            if best is None or c < best[0]:
                best = (c, name, order_t, new, st)
        if best is None:  # no candidate meets D: return the guardrail, unimproved
            g = guard if guard is not None else self._guardrail(scheduling_input)
            order = [idx_t[t] for t in g.task_order]
            new = [idx_r[g.resource_assignments[md.tasks[i]]] for i in range(len(md.tasks))]
            best = (sum(md.c[i][new[i]] for i in range(len(new))), "guardrail_dcr_v1_admission",
                    list(g.task_order), new, {"improve_skipped": "no_candidate_meets_deadline"})
        c, name, order_t, new, st = best
        mapping = {md.tasks[i]: md.resources[new[i]] for i in range(len(md.tasks))}
        stats = dict(st, candidates=tried, chosen=name, internal_compute_cost_ncu=c,
                     internal_makespan_us=_Simulator(md, [idx_t[t] for t in order_t]).makespan(new))
        return AlgorithmDecision(tuple(order_t), mapping, stats)
