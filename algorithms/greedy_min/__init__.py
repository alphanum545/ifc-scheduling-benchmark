"""Classic greedy minimisation baselines (Sakellariou et al., 2007) on DCR's calendar.

  LOSS1MakespanScheduler   min makespan s.t. cost <= B: start from HEFT-IFC; while over budget, apply
                           the cheaper reassignment with the smallest (p_new - p_cur) / (c_cur - c_new).
  DeadlineLossCostScheduler  min cost s.t. makespan <= D: start from HEFT-IFC; repeatedly try the cheaper
                           reassignment with the smallest (p_new - p_cur) / (c_cur - c_new) and keep it
                           if the re-timed makespan is still <= D (same loop as DCR-Min v2's polish).

Both keep HEFT-IFC's task order and re-time with algorithms/dcr_min_v2/calendar.py; neither calls the
Dataset evaluator. They are comparators for the minimisation study, not proposed methods.
"""
from __future__ import annotations

import heapq
from fractions import Fraction

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from algorithms.dcr_ifc.model import Model
from algorithms.dcr_min_v2.scheduler import _decision, _indices, polish_cost
from algorithms.heft_ifc import HeftIFCScheduler

__all__ = ["LOSS1MakespanScheduler", "DeadlineLossCostScheduler"]


class LOSS1MakespanScheduler:
    algorithm_id = "loss1_makespan"
    algorithm_version = "loss1_makespan_20261103_impl1"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("deterministic; seed=None only")
        md, B = Model.create(scheduling_input), scheduling_input.budget_ncu
        order, cur = _indices(md, HeftIFCScheduler().schedule(scheduling_input))
        n, m = len(cur), len(md.resources)
        cost = sum(md.c[i][cur[i]] for i in range(n))
        heap, moves = [], 0

        def push(i):
            for r in range(m):
                dc = md.c[i][cur[i]] - md.c[i][r]
                if dc > 0:
                    heapq.heappush(heap, (Fraction(md.p[i][r] - md.p[i][cur[i]], dc), i, r, cur[i]))
        for i in range(n):
            push(i)
        while cost > B and heap:
            _, i, r, was = heapq.heappop(heap)
            if cur[i] != was:
                continue
            cost, cur[i], moves = cost - md.c[i][was] + md.c[i][r], r, moves + 1
            push(i)
        return _decision(md, order, cur, {"loss1_moves": moves, "internal_compute_cost_ncu": cost})


class DeadlineLossCostScheduler:
    algorithm_id = "deadline_loss_cost"
    algorithm_version = "deadline_loss_cost_20261103_impl1"
    evals_per_task = 10

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("deterministic; seed=None only")
        md, D = Model.create(scheduling_input), scheduling_input.deadline_us
        order, start = _indices(md, HeftIFCScheduler().schedule(scheduling_input))
        cur, cost, ms, evals, moves = polish_cost(md, order, start, D, max(200, self.evals_per_task * len(order)))
        return _decision(md, order, cur, {"dloss_evals": evals, "dloss_moves": moves, "internal_makespan_us": ms,
                                          "internal_compute_cost_ncu": cost, "heft_start_meets_D": moves > 0 or ms <= D})
