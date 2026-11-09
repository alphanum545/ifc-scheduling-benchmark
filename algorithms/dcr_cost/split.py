"""Deterministic deadline-distribution candidate for the DCR-Cost portfolio (paper 2, step 4).

The classical deadline-distribution idea (Yu et al. 2005; IC-PCP, Abrishami et al. 2013; ProLiS, Wu et al.
2017): give every task a sub-deadline proportional to its position on the rank scale, then place it on the
cheapest resource that finishes by that sub-deadline, else on the earliest-finishing one.

Deterministic variant used here: rank_lambda(i) = fast_i + max over children (rank_lambda(c) + lambda * comm_ic),
with fast_i = min_r p_ir and comm the route-aware average communication of the pinned Dataset primitive.
lambda replaces ProLiS's random edge inclusion: lambda = 1 keeps every transfer (the plain upward rank),
lambda = 0 drops them all, and 1/2 sits between. The grid is predeclared, not tuned:
SPLIT_GRID = (0, 1/2, 1).

Sub-deadline: sd_i = D * (R - rank_i + fast_i) / R, with R the largest entry rank (ProLiS Eq. 13).
Order: non-increasing rank (topological, since every execution time is positive).
Placement timing uses the pinned insertion primitive, so it matches the authoritative evaluator.
"""
from __future__ import annotations

from fractions import Fraction

from generator.reference_schedulers import _candidate_assignment, _commit_assignment, _graph, _upward_ranks

SPLIT_GRID = (Fraction(0), Fraction(1, 2), Fraction(1))


def deadline_split(instance: dict, D: int, lam: Fraction) -> tuple[list[str], dict[str, str], int, int]:
    """Return (task order, mapping, internal makespan, internal cost)."""
    g = _graph(instance)
    _, _, avg_comm = _upward_ranks(instance, g)
    exe = instance["execution_time_us"]
    cost = instance["compute_cost_ncu"]
    fast = {t: min(int(exe[t][r]) for r in g.resource_ids) for t in g.task_ids}
    rank: dict[str, Fraction] = {}
    for t in reversed(g.topological_order):
        tail = Fraction(0)
        for c in g.children[t]:
            tail = max(tail, rank[c] + lam * avg_comm[f"{t}->{c}"])
        rank[t] = fast[t] + tail
    R = max(rank.values())
    sd = {t: D * (R - rank[t] + fast[t]) / R for t in g.task_ids}
    pos = {t: k for k, t in enumerate(g.topological_order)}
    order = sorted(g.task_ids, key=lambda t: (-rank[t], pos[t]))
    assignments, intervals, mapping = {}, {}, {}
    for t in order:
        cands = [_candidate_assignment(instance, g, task_id=t, resource_id=r, assignments=assignments,
                                       intervals_by_resource=intervals) for r in g.resource_ids]
        ok = [a for a in cands if a["end_us"] <= sd[t]]
        if ok:
            best = min(ok, key=lambda a: (int(cost[t][a["resource_id"]]), a["end_us"], a["resource_id"]))
        else:
            best = min(cands, key=lambda a: (a["end_us"], int(cost[t][a["resource_id"]]), a["resource_id"]))
        _commit_assignment(assignments, intervals, best)
        mapping[t] = best["resource_id"]
    ms = max(a["end_us"] for a in assignments.values())
    return order, mapping, ms, sum(int(cost[t][r]) for t, r in mapping.items())
