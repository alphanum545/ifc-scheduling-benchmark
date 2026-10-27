"""DCR-v4R: DCR-v4 first, the frozen DCR-v3 rescue portfolio only if v4's own plan fails.

Frozen 2026-10-27 (docs/proposed/DCR_V4R_FREEZE_2026-10-27.md). No new policy, rule or
parameter: both parts are already frozen and measured.

1. Run DCR-v4 (algorithms/dcr_ifc_v4). If its own insertion-calendar plan meets the public
   deadline and budget (the v3 self-check, plan_is_jointly_feasible), return that exact decision.
   The same is done when the cheapest possible cost already exceeds the budget (nothing can help).
2. Otherwise run DCR-v3 Rescue unchanged. If v3's chosen plan meets both limits, return it.
3. Otherwise return DCR-v4's decision.

Hence DCR-v4R never loses a case that DCR-v4 or DCR-v3 solves, whenever the policy-internal
calendars agree with the Dataset evaluator (they did on every stored instance). Worst case:
one DCR-v4 run plus DCR-v3's at most 13 runs of the v1-class step loop, i.e. at most 14 runs,
O(14 (n^2 m + e m + n m log m)) = O(n^2 m + e m + n m log m). No Dataset evaluation is done here.
"""
from __future__ import annotations

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from algorithms.dcr_ifc_v4 import DCRV4QualityScheduler

from ifc_algorithms.proposed.dcr_v2_rules import plan_is_jointly_feasible
from ifc_algorithms.proposed.dcr_v3_rescue import DCRV3RescueScheduler

DESIGN_VERSION = "dcr_ifc_v4_rescue_freeze_20261027"


class DCRV4RescueScheduler:
    algorithm_id = "dcr_ifc_v4_rescue"
    algorithm_version = "dcr_ifc_v4_rescue_freeze_20261027_impl1"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR-v4R is deterministic and accepts seed=None only")
        deadline, budget = scheduling_input.deadline_us, scheduling_input.budget_ncu
        primary = DCRV4QualityScheduler().schedule(scheduling_input)
        pstats = primary.internal_statistics
        chosen, name, runs = primary, "dcr_v4", 1
        if (not plan_is_jointly_feasible(pstats, deadline_us=deadline, budget_ncu=budget)
                and not pstats.get("input_budget_lower_bound_exceeds_budget")):
            rescue = DCRV3RescueScheduler().schedule(scheduling_input)
            rstats = rescue.internal_statistics
            runs += int(rstats.get("portfolio_policy_runs", 1))
            if plan_is_jointly_feasible(rstats, deadline_us=deadline, budget_ncu=budget):
                chosen, name = rescue, f"dcr_v3:{rstats.get('portfolio_selected')}"
            else:
                name = "dcr_v4_no_rescue_found"
        stats = dict(chosen.internal_statistics)
        stats.update({
            "v4r_design_version": DESIGN_VERSION,
            "v4r_selected": name,
            "v4r_policy_runs": runs,
            "v4_internal_makespan_us": pstats.get("internal_makespan_us"),
        })
        return AlgorithmDecision(chosen.task_order, dict(chosen.resource_assignments), stats)
