"""Candidate C (complexity option A): champion-first rescue portfolio.

1. Run the accepted champion unchanged. If its own insertion-calendar plan meets the
   public deadline and budget, return that exact decision (no regression possible
   when the calendar matches Dataset, observed 24/24 on the core suite).
2. Otherwise run a fixed, predeclared list of member policies in order and return the
   first whose own plan meets both limits; if none does, return the champion decision.

Worst case: K = 13 runs of the champion-class policy, O(K * (n^2 m + e m + n m log m)).
K is a constant, so the asymptotic class is unchanged; the extra runs happen only when
the champion's plan is infeasible. Design and in-sample caveat:
docs/superpowers/specs/2026-09-30-dcr-v2-fallback-design.md (Addendum).
No Dataset evaluation is performed here; the self-check uses policy-internal values.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Callable

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from algorithms.dcr_ifc_v1.scheduler import DCRV1AdmissionScheduler

from .dcr_v2 import DCRV2GradedScheduler, DCRV2SparingScheduler, DeadlineCertainlyLost, _DCRV2Base
from .dcr_v2_members import PressureGatedScheduler, TaskPacingScheduler, fraction_label
from .dcr_v2_rules import plan_is_jointly_feasible

DESIGN_VERSION = "dcr_ifc_v3_rescue_design_20260930"
GRID = (Fraction(3), Fraction(2), Fraction(3, 2), Fraction(5, 4), Fraction(1))


def _portfolio() -> list[tuple[str, Callable[[], object]]]:
    members: list[tuple[str, Callable[[], object]]] = [
        ("champion", DCRV1AdmissionScheduler),
        ("graded", DCRV2GradedScheduler),
        ("sparing", DCRV2SparingScheduler),
    ]
    members += [(f"task_pacing_{fraction_label(a)}", lambda a=a: TaskPacingScheduler(a)) for a in GRID]
    members += [(f"pressure_gated_{fraction_label(k)}", lambda k=k: PressureGatedScheduler(k)) for k in GRID]
    return members


def portfolio_names() -> list[str]:
    return [name for name, _ in _portfolio()]


class DCRV3RescueScheduler:
    algorithm_id = "dcr_ifc_v3_rescue"
    # impl2: exact early stop for members (decisions identical to impl1 by construction).
    algorithm_version = "dcr_ifc_v3_rescue_design_20260930_impl2"

    def __init__(self, early_stop: bool = True) -> None:
        self.early_stop = early_stop

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR v3 rescue is deterministic and accepts seed=None only")
        deadline, budget = scheduling_input.deadline_us, scheduling_input.budget_ncu
        members = _portfolio()
        # The champion always runs to completion: its decision is the fallback answer.
        champion = members[0][1]().schedule(scheduling_input)
        chosen, name, tried = champion, "champion", 1
        champ_stats = champion.internal_statistics
        errors: list[str] = []
        stopped: list[str] = []
        stop_steps: list[int] = []
        if (not plan_is_jointly_feasible(champ_stats, deadline_us=deadline, budget_ncu=budget)
                and not champ_stats.get("input_budget_lower_bound_exceeds_budget")):
            chosen, name = champion, "champion_no_rescue_found"
            for member_name, factory in members[1:]:
                tried += 1
                member = factory()
                if self.early_stop and isinstance(member, _DCRV2Base):
                    member.abort_when_deadline_lost = True
                try:
                    decision = member.schedule(scheduling_input)
                except DeadlineCertainlyLost as lost:
                    # Its plan would fail the self-check anyway; skipping is exact.
                    stopped.append(member_name)
                    stop_steps.append(lost.step)
                    continue
                except (ArithmeticError, ValueError):
                    # A member's internal invariant must never cost the champion's valid
                    # schedule; skip it and keep searching.
                    errors.append(member_name)
                    continue
                if plan_is_jointly_feasible(decision.internal_statistics,
                                            deadline_us=deadline, budget_ncu=budget):
                    chosen, name = decision, member_name
                    break
        stats = dict(chosen.internal_statistics)
        stats.update({
            "portfolio_design_version": DESIGN_VERSION,
            "portfolio_selected": name,
            "portfolio_members_tried": tried,
            "portfolio_member_errors": errors,
            "portfolio_early_stop": self.early_stop,
            "portfolio_members_stopped_early": stopped,
            "portfolio_early_stop_steps": stop_steps,
            "portfolio_size": len(members),
            # Honest workload accounting across the whole portfolio, not just the
            # chosen member: each run after the first is a full-schedule rebuild.
            "portfolio_policy_runs": tried,
            "full_schedule_rebuilds_inside_policy": tried - 1,
            "champion_internal_makespan_us": champ_stats.get("internal_makespan_us"),
        })
        return AlgorithmDecision(chosen.task_order, dict(chosen.resource_assignments), stats)
