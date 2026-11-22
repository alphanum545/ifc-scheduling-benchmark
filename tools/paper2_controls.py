"""Predeclared controls for the frozen DCR-Cost v3 evidence study (single worker)."""

from fractions import Fraction
from itertools import count
from time import perf_counter_ns
from unittest.mock import patch

from algorithms.common.interface import AlgorithmDecision
from algorithms.dcr_cost.scheduler import DCRCostSplitScheduler, _Simulator, improve
from algorithms.dcr_cost.split import deadline_split, prepare
from algorithms.dcr_cost_v3 import scheduler as v3
from algorithms.dcr_ifc.model import Model


class PricingOnly(v3.DCRCostPricedScheduler):
    algorithm_id = "paper2-pricing-only"
    algorithm_version = "1"

    def schedule(self, inp):
        # Execute the frozen implementation up to its final polish.
        with patch.object(
            v3, "deep_improve", lambda model, order, assignment: (assignment, {})
        ):
            return super().schedule(inp)


class PolishOnly(v3.DCRCostPricedScheduler):
    algorithm_id = "paper2-polish-only"
    algorithm_version = "1"

    def schedule(self, inp):
        with patch.object(v3, "K_GRID", ()):
            return super().schedule(inp)


class EqualTime:
    """Give the original v2 approach v3's measured wall time on this same instance.

    Use nested refinements of v2's split grid. Only incumbents *available by the
    cutoff* count. A late-finishing candidate is discarded. Physical wall time
    can exceed the cutoff by one operation; both are saved in the raw rows.
    """

    algorithm_id = "paper2-equal-time-v2"
    algorithm_version = "1"

    def __init__(self, limit_ns):
        self.limit_ns = limit_ns

    def schedule(self, inp):
        stop = perf_counter_ns() + self.limit_ns
        best = DCRCostSplitScheduler().schedule(inp)
        self.available = perf_counter_ns() <= stop
        self.trials = 0
        if not self.available:
            return best  # retained for audit; excluded as unavailable at cutoff
        md = Model.create(inp)
        it = {t: i for i, t in enumerate(md.tasks)}
        ir = {r: i for i, r in enumerate(md.resources)}
        best_cost = best.internal_statistics["internal_compute_cost_ncu"]
        best_ok = best.internal_statistics["internal_makespan_us"] <= md.D
        prepared = prepare(inp.instance)

        def accept(order, assignment, ms, cost):
            nonlocal best, best_ok, best_cost
            if ms <= md.D and (not best_ok or cost < best_cost):
                candidate = AlgorithmDecision(tuple(order), assignment)
                if perf_counter_ns() <= stop:
                    best, best_ok, best_cost = candidate, True, cost

        for level in count(2):
            for numerator in range(1, 2**level, 2):
                if perf_counter_ns() >= stop:
                    return best
                order, mapping, ms, cost = deadline_split(
                    inp.instance, md.D, Fraction(numerator, 2**level), prepared
                )
                self.trials += 1
                if perf_counter_ns() >= stop:
                    return best
                if ms > md.D:
                    continue
                accept(order, mapping, ms, cost)
                ix = [it[t] for t in order]
                assign = [ir[mapping[t]] for t in md.tasks]
                better, _ = improve(md, ix, assign)
                if perf_counter_ns() >= stop:
                    return best
                ms = _Simulator(md, ix).makespan(better)
                cost = sum(md.c[i][q] for i, q in enumerate(better))
                accept(
                    order,
                    {t: md.resources[better[i]] for i, t in enumerate(md.tasks)},
                    ms,
                    cost,
                )
