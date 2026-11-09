"""ProLiS (Wu et al., IEEE TPDS 28(12), 2017) adapted to the fixed IFC v1 model (paper 2 comparator).

Audit and every adaptation decision: docs/paper_audits/PROLIS_2017.md (MAJOR MODEL ADAPTATION).
Kept: probabilistic upward rank (Eqs. 11-12, theta = 1.5), deadline distribution (Eq. 13), ordering by
probabilistic upward rank, and selection of the cheapest resource meeting the sub-deadline, else the earliest
finish (Algorithm 1). Removed (not representable): new instances, interval billing, type upgrades.
Timing uses the pinned Dataset insertion primitive; static communication uses the route-aware average, as in
the companion paper's BDC/BDDC ports.
"""
from __future__ import annotations

import random
from fractions import Fraction

from generator.reference_schedulers import (
    _candidate_assignment,
    _commit_assignment,
    _graph,
    _upward_ranks,
)

from algorithms.common.interface import AlgorithmDecision, AlgorithmInput

THETA = 1.5  # paper Table III


class ProLiSScheduler:
    algorithm_id = "prolis_ifc"
    algorithm_version = "prolis_ifc_audit_20261109_impl1"

    def __init__(self, seed: int = 0) -> None:
        self.default_seed = seed

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        rng = random.Random(self.default_seed if seed is None else seed)
        inst = scheduling_input.instance
        g = _graph(inst)
        _, _, avg_comm = _upward_ranks(inst, g)
        exe = inst["execution_time_us"]
        fast = {t: min(int(exe[t][r]) for r in g.resource_ids) for t in g.task_ids}  # w_i / p(s*)

        # Eqs. (11)-(12): probabilistic upward rank.
        pr: dict[str, Fraction] = {}
        for t in reversed(g.topological_order):
            tail = Fraction(0)
            for c in g.children[t]:
                comm = avg_comm[f"{t}->{c}"]
                if comm > 0:
                    ccr = Fraction(fast[c]) / comm
                    gamma = 0 if (1 - THETA ** (-float(ccr))) < rng.random() else 1
                else:
                    gamma = 1
                tail = max(tail, pr[c] + gamma * comm)
            pr[t] = fast[t] + tail
        pr_entry = max(pr[t] for t in g.task_ids if not g.parents[t])  # dummy zero-cost entry
        D = scheduling_input.deadline_us
        psd = {t: D * (pr_entry - pr[t] + fast[t]) / pr_entry for t in g.task_ids}  # Eq. (13)

        order = sorted(g.task_ids, key=lambda t: (-pr[t], t))  # topological: pr_parent > pr_child
        cost = inst["compute_cost_ncu"]
        assignments, intervals, mapping = {}, {}, {}
        for t in order:
            cands = [_candidate_assignment(inst, g, task_id=t, resource_id=r, assignments=assignments,
                                           intervals_by_resource=intervals) for r in g.resource_ids]
            meeting = [a for a in cands if a["end_us"] <= psd[t]]
            if meeting:
                best = min(meeting, key=lambda a: (int(cost[t][a["resource_id"]]), a["end_us"], a["resource_id"]))
            else:
                best = min(cands, key=lambda a: (a["end_us"], int(cost[t][a["resource_id"]]), a["resource_id"]))
            _commit_assignment(assignments, intervals, best)
            mapping[t] = best["resource_id"]
        stats = {"theta": THETA, "seed": self.default_seed if seed is None else seed,
                 "internal_makespan_us": max(a["end_us"] for a in assignments.values()),
                 "internal_compute_cost_ncu": sum(int(cost[t][r]) for t, r in mapping.items())}
        return AlgorithmDecision(tuple(order), mapping, stats)
