"""Pure per-step choice rules for the DCR-v2 candidates.

Each function is O(m) over the candidate resources of a single step and uses only
values the scheduler has already computed for that step (see the complexity ledger
in docs/superpowers/specs/2026-09-30-dcr-v2-fallback-design.md).
"""
from __future__ import annotations

from fractions import Fraction
from typing import Sequence


def relaxed_choice(relaxed: Sequence[tuple[int, int, int, int]]) -> int | None:
    """Candidate A: least violation of the priced reserve certificate.

    `relaxed` holds (bound, finish, cost, resource) for candidates that passed every
    structural screen but failed `bound <= H*B`. Returns the resource index, or None.
    """
    if not relaxed:
        return None
    return min(relaxed)[3]


def champion_fallback_choice(allowed: Sequence[int], finish: Sequence[int],
                             cost: Sequence[int]) -> int:
    """Champion rule: earliest finish, then cost, then resource index."""
    return min(allowed, key=lambda r: (finish[r], cost[r], r))


def sparing_fallback_choice(allowed: Sequence[int], finish: Sequence[int],
                            cost: Sequence[int], *, latest_finish: int) -> int:
    """Candidate B: cheapest resource that still meets the task's latest finish.

    Falls back to the champion rule when no allowed resource is timely.
    """
    timely = [r for r in allowed if finish[r] <= latest_finish]
    if timely:
        return min(timely, key=lambda r: (cost[r], finish[r], r))
    return champion_fallback_choice(allowed, finish, cost)


def task_pacing_admits(extra: int, *, done: int, whole: int, slack0: int, alpha: Fraction) -> bool:
    """Task-count glide path: extra spend <= slack0 * min(1, alpha * done / whole).

    Exact integer comparison; `extra` is cost above the cheapest option, summed over
    scheduled tasks including the candidate placement.
    """
    num, den = alpha.numerator, alpha.denominator
    return extra * whole * den <= slack0 * min(whole * den, num * done)


def pressure_safe(finish: int, *, deadline: int, tail: int, kappa: Fraction) -> bool:
    """True when `finish` leaves room for `kappa` times the task's critical tail."""
    num, den = kappa.numerator, kappa.denominator
    return finish * den <= deadline * den - num * tail


def plan_is_jointly_feasible(stats, *, deadline_us: int, budget_ncu: int) -> bool:
    """Policy-internal self-check on its own insertion calendar (not a Dataset call)."""
    makespan = stats.get("internal_makespan_us")
    cost = stats.get("internal_compute_cost_ncu")
    if makespan is None or cost is None:
        return False
    return makespan <= deadline_us and cost <= budget_ncu
