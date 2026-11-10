"""DCR-Cost v3: DCR-Cost v2 plus time-priced list-scheduling candidates and a deeper final polish (paper 2).

Problem: minimize total compute cost subject to the deadline D (budget ignored), as in algorithms/dcr_cost.

Why: against CP-SAT on the 60-task instances, v2's large gaps (up to 2.2x) are structural. Its candidates
give the first tasks of a wide level the cheapest slow resources and pay for the lost time with the most
expensive resources later; no single downgrade repairs that. A plan that prices time from the start
spreads the slack more evenly.

Added on top of v2 (v2's sources are untouched, so its stored results stay valid):

  1. Time-priced candidates. A list scheduler (ready task with the smallest sigma_i = b_i - pmin_i first;
     exact insertion) places each task on the resource minimizing
            c_ir + mu * t_ir          among resources with finish <= b_i (DCR's latest finish),
     where t_ir is the finish time (mode "finish") or the duration (mode "dur"); if no resource meets
     b_i, the earliest finish. mu = S * 2^k with S = sum_i (cmax_i - cmin_i) / D and k in K_GRID, both
     predeclared: mu = 0 is "cheapest that still fits", large mu is earliest finish.
  2. The TOP_K cheapest distinct priced plans that meet D go through v2's downgrade improvement pass.
  3. The cheapest of {v2's plan, improved priced plans} is polished: the same downgrade move, but every
     pass tries up to DEEP_TRIES cheaper resources per task and passes repeat until no move is found
     (at most DEEP_REBUILDS_PER_TASK * n exact rebuilds).

Dominance: v2's returned plan is always a candidate and the polish only accepts moves that lower cost
and keep the exact rebuild within D, so v3 never costs more than v2 and meets D whenever v2 does.
Deterministic; integer/rational arithmetic only in the new parts.
"""
from __future__ import annotations

from fractions import Fraction

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from algorithms.dcr_cost.scheduler import DCRCostSplitScheduler, _Simulator, improve
from algorithms.dcr_ifc.model import Model

DESIGN_VERSION = "dcr_cost_priced_design_20261110"
K_GRID = tuple(range(-8, 9))
MODES = ("finish", "dur")
TOP_K = 4
DEEP_TRIES = 8
DEEP_REBUILDS_PER_TASK = 10


def priced_plan(md: Model, sim: _Simulator, num: int, den: int, mode: str) -> tuple[list[int], list[int], int]:
    """One time-priced list schedule with mu = num/den. Returns (task order, assignment, makespan).

    Timing equals the evaluator's for the returned order: ready time = max over parents of (parent end +
    tier-route communication, 0 on the same resource), then the earliest idle slot (insertion)."""
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    by_finish = mode == "finish"
    n, m = len(md.tasks), len(md.resources)
    tier_of, comm = sim.tier_of, sim.comm
    tiers = max(tier_of) + 1
    indegree = [len(p) for p in md.parents]
    ready = {i for i in range(n) if not indegree[i]}
    end, assign, order = [0] * n, [0] * n, []
    cals: list[list[tuple[int, int, int]]] = [[] for _ in range(m)]
    while ready:
        i = min(ready, key=lambda j: (md.sigma[j], j))
        ready.remove(i)
        parents = md.parents[i]
        tier_ready = [0] * tiers  # ready time on a resource of each tier that hosts no parent
        for p in parents:
            table, e = comm[p, i][tier_of[assign[p]]], end[p]
            for t in range(tiers):
                d = table[t]
                if d is not None and e + d > tier_ready[t]:
                    tier_ready[t] = e + d
        hosts = {assign[p] for p in parents}
        pi, ci, bi = md.p[i], md.c[i], md.b[i]
        best = fastest = None
        for r in range(m):
            if r in hosts:
                start = 0
                for p in parents:
                    d = 0 if assign[p] == r else comm[p, i][tier_of[assign[p]]][tier_of[r]]
                    if end[p] + d > start:
                        start = end[p] + d
            else:
                start = tier_ready[tier_of[r]]
            dur = pi[r]
            for s, e, _ in cals[r]:
                if start + dur <= s:
                    break
                if start < e:
                    start = e
            f = start + dur
            key = (f, ci[r], r)
            if fastest is None or key < fastest[0]:
                fastest = (key, r, start, f)
            if f <= bi:
                key = (den * ci[r] + num * (f if by_finish else dur), f, r)
                if best is None or key < best[0]:
                    best = (key, r, start, f)
        _, r, s, f = best if best is not None else fastest
        assign[i], end[i] = r, f
        cal, pos = cals[r], 0
        while pos < len(cal) and cal[pos][0] < s:
            pos += 1
        cal.insert(pos, (s, f, i))
        order.append(i)
        for child in md.children[i]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.add(child)
    return order, assign, max(end)


def deep_improve(md: Model, order: list[int], assign: list[int], tries: int = DEEP_TRIES,
                 rebuilds_per_task: int = DEEP_REBUILDS_PER_TASK) -> tuple[list[int], dict]:
    """Downgrade moves to a local optimum: like dcr_cost.improve, but `tries` cheaper resources per task and
    passes until no move is accepted, within a fixed budget of exact rebuilds. A plan that misses D is
    returned unchanged."""
    sim = _Simulator(md, order)
    D, m = md.D, len(md.resources)
    assign = list(assign)
    stats = {"deep_moves": 0, "deep_rebuilds": 0, "deep_saving_ncu": 0, "deep_passes": 0}
    ms, end, cals = sim.run(assign)
    if ms > D:
        stats["deep_skipped"] = "start_plan_misses_deadline"
        return assign, stats
    base, budget = (end, cals), rebuilds_per_task * len(assign)
    moved = True
    while moved and stats["deep_rebuilds"] < budget:
        moved = False
        stats["deep_passes"] += 1
        for i in sorted(range(len(assign)), key=lambda i: (-(md.c[i][assign[i]] - md.cmin[i]), i)):
            cur = assign[i]
            if md.c[i][cur] == md.cmin[i]:
                break  # sorted by possible saving: nothing left to gain from here on
            options = sorted((q for q in range(m) if md.c[i][q] < md.c[i][cur]),
                             key=lambda q: (md.c[i][q], md.p[i][q], q))[:tries]
            for q in options:
                if stats["deep_rebuilds"] >= budget:
                    break
                assign[i] = q
                stats["deep_rebuilds"] += 1
                trial = sim.run(assign, k=sim.pos[i], base=base, limit=D)
                if trial[0] <= D:
                    base = trial[1:]
                    stats["deep_moves"] += 1
                    stats["deep_saving_ncu"] += md.c[i][cur] - md.c[i][q]
                    moved = True
                    break
                assign[i] = cur
    return assign, stats


class DCRCostPricedScheduler(DCRCostSplitScheduler):
    """DCR-Cost v3 = v2's plan, the improved time-priced plans, cheapest one polished. Never costlier than v2."""
    algorithm_id = "dcr_cost_priced"
    algorithm_version = "dcr_cost_priced_design_20261110_impl1"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR-Cost is deterministic and accepts seed=None only")
        v2 = super().schedule(scheduling_input)
        md = Model.create(scheduling_input)
        n, D = len(md.tasks), md.D
        idx_t = {t: i for i, t in enumerate(md.tasks)}
        idx_r = {r: q for q, r in enumerate(md.resources)}

        def cost(assign: list[int]) -> int:
            return sum(md.c[i][assign[i]] for i in range(n))

        v2_order = [idx_t[t] for t in v2.task_order]
        v2_assign = [idx_r[v2.resource_assignments[md.tasks[i]]] for i in range(n)]
        v2_cost = cost(v2_assign)
        v2_ok = _Simulator(md, v2_order).makespan(v2_assign) <= D
        best = (v2_cost, "v2", v2_order, v2_assign)

        tables = _Simulator(md, list(md.topological))  # tier-route communication tables only
        scale = Fraction(sum(max(row) - min(row) for row in md.c), D)
        raw, seen, generated = [], set(), 0
        for mode in MODES:
            for k in K_GRID:
                mu = scale * Fraction(2) ** k
                order, assign, ms = priced_plan(md, tables, mu.numerator, mu.denominator, mode)
                generated += 1
                key = (tuple(order), tuple(assign))
                if ms <= D and key not in seen:
                    seen.add(key)
                    raw.append((cost(assign), len(raw), f"priced_{mode}_k={k}", order, assign))
        raw.sort()
        tried = []
        for c0, _, name, order, assign in raw[:TOP_K]:
            if _Simulator(md, order).makespan(assign) > D:  # exact rebuild disagrees: never use the plan
                tried.append((name, False, c0, None))
                continue
            new, _ = improve(md, order, assign)
            c = cost(new)
            tried.append((name, True, c0, c))
            # a priced plan replaces v2's only if it is strictly cheaper, or v2's plan misses D
            if c < best[0] or (not v2_ok and best[1] == "v2"):
                best = (c, name, order, new)
        c, name, order, assign = best
        polished, deep = deep_improve(md, order, assign)
        if _Simulator(md, order).makespan(polished) <= D:
            assign, c = polished, cost(polished)
        stats = dict(deep, design_version=DESIGN_VERSION, chosen=name, v2_chosen=v2.internal_statistics.get("chosen"),
                     v2_compute_cost_ncu=v2_cost, v2_meets_deadline=v2_ok, priced_generated=generated,
                     priced_feasible_distinct=len(raw), priced_improved=tried, internal_compute_cost_ncu=c,
                     internal_makespan_us=_Simulator(md, order).makespan(assign))
        return AlgorithmDecision(tuple(md.tasks[i] for i in order),
                                 {md.tasks[i]: md.resources[assign[i]] for i in range(n)}, stats)
