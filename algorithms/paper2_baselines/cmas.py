"""CMaS (Pham et al., IJDSN 13(11), 2017) on the fixed IFC v1 model (paper 2 comparator).

Audit and every adaptation decision: docs/paper_audits/CMAS_2017.md (MINOR MODEL ADAPTATION).
Algorithm 1: upward-rank priority (average execution and route-aware average communication), node selection
by the cost-EFT utility U (Eq. 15) with cost = compute_cost_ncu. Algorithm 2: deadline-based reassignment of
critical-path tasks, repeated until the deadline is met or the makespan stops improving. Insertion timing via
the pinned Dataset primitive. Deterministic.
"""
from __future__ import annotations

from fractions import Fraction

from generator.reference_schedulers import (
    _candidate_assignment,
    _commit_assignment,
    _communication_metrics,
    _graph,
    _upward_ranks,
)

from algorithms.common.interface import AlgorithmDecision, AlgorithmInput

MAX_ROUNDS = 64  # safety cap; the paper's stop rule normally ends far earlier


def _utility(cost: int, min_cost: int, eft: int, min_eft: int) -> Fraction:
    """Eq. (15). Convention for free resources (audit): factor 1 if cost == 0; 0 if cost > 0 and min == 0."""
    if cost == 0:
        cf = Fraction(1)
    elif min_cost == 0:
        cf = Fraction(0)
    else:
        cf = Fraction(min_cost, cost)
    return cf * Fraction(min_eft, eft)


class CMaSScheduler:
    algorithm_id = "cmas_ifc"
    algorithm_version = "cmas_ifc_audit_20261109_impl1"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        inst = scheduling_input.instance
        g = _graph(inst)
        rank, _, _ = _upward_ranks(inst, g)
        order = sorted(g.task_ids, key=lambda t: (-rank[t], t))
        cost = {t: {r: int(v) for r, v in row.items()} for t, row in inst["compute_cost_ncu"].items()}
        D = scheduling_input.deadline_us

        def build(fixed_rule):
            """Rebuild in priority order. fixed_rule(t, cands) may return a chosen assignment or None."""
            assignments, intervals = {}, {}
            for t in order:
                cands = [_candidate_assignment(inst, g, task_id=t, resource_id=r, assignments=assignments,
                                               intervals_by_resource=intervals) for r in g.resource_ids]
                choice = fixed_rule(t, cands) if fixed_rule else None
                if choice is None:
                    choice = self._select(t, cands, cost)
                _commit_assignment(assignments, intervals, choice)
            return assignments, intervals

        current, cur_iv = build(None)
        best = current
        rounds = 0
        while rounds < MAX_ROUNDS:
            rounds += 1
            old = self._makespan(current)
            cp = self._critical_path(inst, g, current, cur_iv)
            distance = Fraction(old - D, len(cp))
            sub = {t: current[t]["end_us"] - distance for t in cp}

            def rule(t, cands, sub=sub):
                if t not in sub or sub[t] < 0:
                    return None  # non-critical or not reassigned: node selection (Eq. 15) in line 24
                ok = [a for a in cands if a["end_us"] <= sub[t]]
                if ok:
                    return self._select(t, ok, cost)
                return min(cands, key=lambda a: (a["end_us"], cost[t][a["resource_id"]], a["resource_id"]))

            new, new_iv = build(rule)
            if self._makespan(new) < self._makespan(best) or (
                    self._makespan(new) == self._makespan(best) and self._cost(new, cost) < self._cost(best, cost)):
                best = new
            current, cur_iv = new, new_iv
            if self._makespan(current) <= D or self._makespan(current) >= old:
                break
        final = current if self._makespan(current) <= D else best
        mapping = {t: a["resource_id"] for t, a in final.items()}
        stats = {"reassignment_rounds": rounds, "internal_makespan_us": self._makespan(final),
                 "internal_compute_cost_ncu": self._cost(final, cost)}
        return AlgorithmDecision(tuple(order), mapping, stats)

    @staticmethod
    def _select(t, cands, cost):
        min_cost = min(cost[t][a["resource_id"]] for a in cands)
        min_eft = min(a["end_us"] for a in cands)
        # Max U (Eq. 15); ties by earlier finish, lower cost, then resource id.
        return min(cands, key=lambda a: (-_utility(cost[t][a["resource_id"]], min_cost, a["end_us"], min_eft),
                                         a["end_us"], cost[t][a["resource_id"]], a["resource_id"]))

    @staticmethod
    def _makespan(assignments):
        return max(a["end_us"] for a in assignments.values())

    @staticmethod
    def _cost(assignments, cost):
        return sum(cost[t][a["resource_id"]] for t, a in assignments.items())

    @staticmethod
    def _critical_path(inst, g, assignments, intervals):
        """Walk back from the latest-finishing task through the constraint that fixed each start (audit)."""
        t = max(assignments, key=lambda k: (assignments[k]["end_us"], k))
        path = []
        seen = set()
        while t is not None and t not in seen:
            seen.add(t)
            path.append(t)
            a = assignments[t]
            ready, ready_parent = 0, None
            for p in g.parents[t]:
                pa = assignments[p]
                comm = _communication_metrics(inst, g, parent=p, child=t, source_resource=pa["resource_id"],
                                              target_resource=a["resource_id"])["communication_time_us"]
                if pa["end_us"] + comm > ready or (pa["end_us"] + comm == ready and ready_parent is None):
                    ready, ready_parent = pa["end_us"] + comm, p
            if a["start_us"] == ready:
                t = ready_parent
            else:  # resource-bound: previous task on the same resource
                prev = [iv for iv in intervals[a["resource_id"]] if iv["end_us"] == a["start_us"]]
                t = prev[0]["task_id"] if prev else ready_parent
        return path[::-1]
