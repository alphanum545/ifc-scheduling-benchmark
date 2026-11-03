"""DCR-Min v2: the DCR-Min search with the changes recommended in docs/proposed/DCR_MIN_ANALYSIS.md §8.

  DCRMinV2MakespanScheduler   minimise makespan     s.t. compute cost <= B  (D is ignored)
  DCRMinV2CostScheduler       minimise compute cost s.t. makespan <= D      (B is ignored)

Changes against DCR-Min v1 (algorithms/dcr_min), each from the analysis:
  1. Start probes that never paid off are dropped (B2, B4):
       makespan: the 2x slack probe is removed; the probe goes to the descent.
       cost:     the LB_C(D) probe is removed (it met D on 0/70 traced instances); LB_C(D) stays the
                 lower end of the bisection bracket.
  2. A local polish on DCR's own insertion calendar runs after the search (§6):
       cost:     deadline-LOSS. Repeatedly try the cheaper reassignment with the smallest
                 (p_new - p_cur) / (c_cur - c_new); keep it if the re-timed makespan is still <= D.
       makespan: GAIN. Repeatedly try the faster reassignment with the largest
                 (p_cur - p_new) / max(c_new - c_cur, 1) (moves that also save cost first); keep it if
                 the cost stays <= B and the re-timed makespan strictly drops.
     Task order is the search plan's own (DCR placement order, which is topological). Re-timing uses
     algorithms/dcr_min_v2/calendar.py, the same insertion rule DCR plans with; the Dataset evaluator is
     never called (benchmark rule: final metrics are evaluator-only).
The oracle and every DCR rule are unchanged. Search defaults are unchanged (oracle DCR-v4R; descent
for makespan, bisect for cost; 12 probes in total).

Guarantees: min-makespan's plan respects B whenever sum cmin <= B (DCR's per-step budget screen, then
the polish only accepts moves that keep cost <= B). Min-cost keeps only plans whose calendar makespan is
<= D. The polish never makes the objective worse.

Cost: at most 12 oracle runs plus at most `polish_evals` calendar re-timings, each O(n + e + n·k)
with k tasks per resource calendar.
"""
from __future__ import annotations

import heapq
from fractions import Fraction

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from algorithms.dcr_ifc.model import Model
from algorithms.dcr_min.scheduler import _Search, lower_bounds

from .calendar import Calendar

DESIGN_VERSION = "dcr_min_v2_design_20261103"


def _indices(md: Model, dec: AlgorithmDecision) -> tuple[list[int], list[int]]:
    ti = {t: k for k, t in enumerate(md.tasks)}
    ri = {r: k for k, r in enumerate(md.resources)}
    return [ti[t] for t in dec.task_order], [ri[dec.resource_assignments[t]] for t in md.tasks]


def _decision(md: Model, order: list[int], assign: list[int], stats: dict) -> AlgorithmDecision:
    return AlgorithmDecision(tuple(md.tasks[i] for i in order),
                             {md.tasks[i]: md.resources[assign[i]] for i in range(len(assign))}, stats)


def polish_cost(md: Model, order: list[int], assign: list[int], D: int, max_evals: int):
    """Deadline-LOSS on the calendar. Returns (assign, cost, makespan, evals, moves)."""
    cal, cur = Calendar(md, order), list(assign)
    n, m = len(cur), len(md.resources)
    ms, evals, moves, heap = cal.makespan(cur), 1, 0, []

    def push(i):
        for r in range(m):
            dc = md.c[i][cur[i]] - md.c[i][r]
            if dc > 0:
                heapq.heappush(heap, (Fraction(md.p[i][r] - md.p[i][cur[i]], dc), i, r, cur[i]))
    if ms <= D:
        for i in range(n):
            push(i)
    while heap and evals < max_evals:
        _, i, r, was = heapq.heappop(heap)
        if cur[i] != was:
            continue
        cur[i] = r
        new = cal.makespan(cur, cap=D)
        evals += 1
        if new <= D:
            ms, moves = new, moves + 1
            push(i)
        else:
            cur[i] = was
    return cur, sum(md.c[i][cur[i]] for i in range(n)), ms, evals, moves


def polish_makespan(md: Model, order: list[int], assign: list[int], B: int, max_evals: int):
    """GAIN on the calendar. Returns (assign, cost, makespan, evals, moves)."""
    cal, cur = Calendar(md, order), list(assign)
    n, m = len(cur), len(md.resources)
    cost = sum(md.c[i][cur[i]] for i in range(n))
    ms, evals, moves, heap = cal.makespan(cur), 1, 0, []

    def push(i):
        for r in range(m):
            dp, dc = md.p[i][cur[i]] - md.p[i][r], md.c[i][r] - md.c[i][cur[i]]
            if dp > 0:
                heapq.heappush(heap, ((0, -dp, 0) if dc <= 0 else (1, -Fraction(dp, dc), dc), i, r, cur[i]))
    if cost <= B:
        for i in range(n):
            push(i)
    while heap and evals < max_evals:
        _, i, r, was = heapq.heappop(heap)
        dc = md.c[i][r] - md.c[i][was]
        if cur[i] != was or cost + dc > B:
            continue
        cur[i] = r
        new = cal.makespan(cur, cap=ms - 1)
        evals += 1
        if new < ms:
            ms, cost, moves = new, cost + dc, moves + 1
            push(i)
        else:
            cur[i] = was
    return cur, cost, ms, evals, moves


class _V2:
    polish = True
    polish_evals_per_task = 10

    def _budget(self, n: int) -> int:
        return max(200, self.polish_evals_per_task * n)


class DCRMinV2MakespanScheduler(_V2, _Search):
    algorithm_id = "dcr_min_v2_makespan"
    algorithm_version = "dcr_min_v2_makespan_design_20261103_impl1"
    strategy = "descent"

    def __init__(self, oracle=None, *, strategy=None, max_probes=None, polish=None):
        super().__init__(oracle, strategy=strategy, max_probes=max_probes)
        if polish is not None:
            self.polish = polish

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR-Min v2 is deterministic and accepts seed=None only")
        B = scheduling_input.budget_ncu
        lb = lower_bounds(scheduling_input)
        log: list = []
        if lb["cost_lb_ncu"] > B:
            dec, _, _ = self._probe(scheduling_input, log, deadline_us=lb["makespan_lb_us"])
            return self._finish(dec, {**lb, "probes": log, "status": "budget_infeasible"})
        best: list = []

        def run(deadline: int):
            dec, ms, cost = self._probe(scheduling_input, log, deadline_us=deadline)
            ok = ms is not None and cost is not None and cost <= B
            improved = ok and (not best or (ms, cost) < tuple(best[:2]))
            if improved:
                best[:] = [ms, cost, dec]
            return improved, ok and ms <= deadline

        run(lb["makespan_lb_us"])
        if not best:  # unreachable while DCR's raw budget invariant holds; kept as a guard
            dec, _, _ = self._probe(scheduling_input, log)
            return self._finish(dec, {**lb, "probes": log, "status": "no_budget_feasible_probe"})
        self._search(lb["makespan_lb_us"], lambda: best[0], run, log)
        extra = {**lb, "probes": log, "status": "ok", "search_makespan_us": best[0], "search_cost_ncu": best[1]}
        dec = best[2]
        if self.polish:
            md = Model.create(scheduling_input)
            order, assign = _indices(md, dec)
            assign, cost, ms, evals, moves = polish_makespan(md, order, assign, B, self._budget(len(order)))
            extra.update(polish_evals=evals, polish_moves=moves)
            if moves:
                stats = dict(dec.internal_statistics, internal_makespan_us=ms, internal_compute_cost_ncu=cost)
                dec = _decision(md, order, assign, stats)
        out = self._finish(dec, extra)
        out.internal_statistics["dcrmin_design_version"] = DESIGN_VERSION
        return out


class DCRMinV2CostScheduler(_V2, _Search):
    algorithm_id = "dcr_min_v2_cost"
    algorithm_version = "dcr_min_v2_cost_design_20261103_impl1"
    strategy = "bisect"

    def __init__(self, oracle=None, *, strategy=None, max_probes=None, polish=None):
        super().__init__(oracle, strategy=strategy, max_probes=max_probes)
        if polish is not None:
            self.polish = polish

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR-Min v2 is deterministic and accepts seed=None only")
        D = scheduling_input.deadline_us
        lb = lower_bounds(scheduling_input)
        log: list = []
        best: list = []
        fastest: list = []

        def run(budget: int):
            dec, ms, cost = self._probe(scheduling_input, log, budget_ncu=budget)
            if ms is None or cost is None:
                return False, False
            if not fastest or (ms, cost) < tuple(fastest[:2]):
                fastest[:] = [ms, cost, dec]
            improved = ms <= D and (not best or (cost, ms) < tuple(best[:2]))
            if improved:
                best[:] = [cost, ms, dec]
            return improved, ms <= D and cost <= budget

        if lb["cost_lb_deadline_ncu"] is None:
            run(lb["cost_max_ncu"])
            return self._finish(fastest[2], {**lb, "probes": log, "status": "deadline_certified_infeasible"})
        run(lb["cost_max_ncu"])
        if not best:
            return self._finish(fastest[2], {**lb, "probes": log, "status": "deadline_not_met"})
        self._search(lb["cost_lb_deadline_ncu"], lambda: best[0], run, log)
        extra = {**lb, "probes": log, "status": "ok", "search_cost_ncu": best[0], "search_makespan_us": best[1]}
        dec = best[2]
        if self.polish:
            md = Model.create(scheduling_input)
            order, assign = _indices(md, dec)
            assign, cost, ms, evals, moves = polish_cost(md, order, assign, D, self._budget(len(order)))
            extra.update(polish_evals=evals, polish_moves=moves)
            if moves:
                stats = dict(dec.internal_statistics, internal_makespan_us=ms, internal_compute_cost_ncu=cost)
                dec = _decision(md, order, assign, stats)
        out = self._finish(dec, extra)
        out.internal_statistics["dcrmin_design_version"] = DESIGN_VERSION
        return out
