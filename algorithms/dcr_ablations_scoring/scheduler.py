"""Scoring ablation of DCR-v1 Admission (paper 1), predeclared 2026-10-27.

Question: does DCR's gain come only from its deadline-aware reserve (admission), or also from
ranking admitted candidates by the fraction of remaining time and budget *slack* they consume?

This module is a separate copy of the DCR-v1 Admission step loop, as used by
algorithms/dcr_ablations (DESIGN 20261024), so that the existing ablation sources and their
stored results are untouched. Exactly one component differs between the two variants here:

  scoring-control  ranks admitted candidates with DCR's minimax slack loss
                   (max(time_loss, budget_loss), min(...), finish, cost, resource);
                   must reproduce DCR-v1 Admission decisions exactly (faithfulness check).
  bdc-score        ranks the SAME admitted candidates by BDC's Quality (Taghinezhad-Niar et al.
                   2021, Eqs. 13-15, as implemented in algorithms/bddc_bdc), omega = 1/2:
                     TQ = (SDL - FT - FT_min) / SDL      SDL    = task latest finish b_i
                     CQ = (RB  - TC - TC_min) / RB       RB     = whole remaining budget B - spent
                     Q  = (TQ + CQ) / 2, highest first; ties (finish, cost, resource).
                   b_i (deadline minus the critical tail) is DCR's per-task counterpart of BDC's
                   level sub-deadline; BDC normalizes cost by the whole remaining budget.
                   RB = 0 (only possible when every remaining cost is 0) gives CQ = 0.

Unchanged in both: priced reserve admission with the exact child-arrival correction, the three
dual price vectors, the raw budget invariant, latest-finish/domain/capacity time screens, task
priority, and the budget-safe fallback.
"""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256

from generator.canonical import canonical_json_bytes
from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from algorithms.dcr_ifc.model import Model
from algorithms.dcr_ifc_optimized.state import State
from algorithms.dcr_ifc_v1.reserve import ReservePool
from algorithms.dcr_ifc_v1.scheduler import loss

DESIGN_VERSION = "dcr_ablations_scoring_paper1_design_20261027"


class _ScoringBase:
    algorithm_id = "dcr_abl_scoring_base"
    algorithm_version = "dcr_abl_scoring_base_design_20261027_impl1"
    rank = "minimax"  # minimax | bdc

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR ablations are deterministic and accept seed=None only")
        md = Model.create(scheduling_input)
        st = State(md)
        m = len(md.resources)
        HB = md.H * md.B
        stats: dict[str, object] = {
            "design_version": DESIGN_VERSION, "baseline_lineage": "dcr_ifc_v1_arrival_design_20260907_admission1",
            "rank": self.rank, "candidate_count": 0, "screened_candidate_count": 0, "reject_reserve_bound": 0,
            "first_fallback_step": None, "first_fallback_reason": None, "fallback_task_count": 0,
            "input_budget_lower_bound_exceeds_budget": False,
        }
        if st.raw_reserve > md.B:
            stats["input_budget_lower_bound_exceeds_budget"] = True
            mapping = {md.tasks[i]: md.resources[min(range(m), key=lambda r: (md.c[i][r], md.p[i][r], r))]
                       for i in md.topological}
            return AlgorithmDecision(tuple(md.tasks[i] for i in md.topological), mapping, stats)
        pool = None
        fallback = False
        while st.U:
            i = st.choose_task()
            placements = [st.insertion(i, r) for r in range(m)]
            f0 = min(f for _, f in placements)
            budget_allowed = [r for r in range(m) if
                              st.spent + md.c[i][r] + st.raw_reserve - md.cmin[i] <= md.B]
            if not budget_allowed:
                raise ArithmeticError("raw budget invariant lost a cheapest-resource option")
            stats["candidate_count"] += m
            screened = []
            reason = "empty_screen"
            if not fallback:
                if any(st.count[j] == 0 for j in st.U):
                    reason = "empty_current_domain"
                else:
                    if len(st.order) in md.epochs:
                        pool = ReservePool(st)
                    if pool is None:
                        raise ArithmeticError("uninitialized price pool")
                    pool.refresh_minima(st)
                    stime, sbudget = md.b[i] - f0, HB - pool.current
                    if stime < 0:
                        reason = "negative_time_margin"
                    elif sbudget < 0:
                        reason = "current_reserve_exceeds_budget"
                    else:
                        candidates = {}
                        for r in budget_allowed:
                            s, f = placements[r]
                            if not st.active[i][r] or f > md.b[i]:
                                continue
                            deleted = st.capacity_deletions(i, r, s, f)
                            if deleted is None:
                                continue
                            candidates[r] = deleted
                        pool.prepare(st, i, placements, candidates)
                        remaining_budget = md.B - st.spent
                        for r, deleted in candidates.items():
                            s, f = placements[r]
                            bounds = pool.candidate_bounds(st, i, r, s, f, deleted)
                            if bounds is None:
                                continue
                            capacity_bound, bound = bounds
                            if bound > HB:
                                stats["reject_reserve_bound"] += 1
                                continue
                            if self.rank == "minimax":
                                pt, pb = loss(f - f0, stime), loss(capacity_bound - pool.current, sbudget)
                                key = (max(pt, pb), min(pt, pb), f, md.c[i][r], r)
                            elif self.rank == "bdc":
                                sdl = md.b[i]
                                tq = Fraction(sdl - f - f0, sdl)
                                cq = (Fraction(remaining_budget - md.c[i][r] - md.cmin[i], remaining_budget)
                                      if remaining_budget > 0 else Fraction(0))
                                key = (-(tq + cq) / 2, f, md.c[i][r], r)
                            else:
                                raise ValueError(self.rank)
                            screened.append((key, r))
                stats["screened_candidate_count"] += len(screened)
            if screened:
                r = min(screened)[1]
            else:
                r = min(budget_allowed, key=lambda q: (placements[q][1], md.c[i][q], q))
                if not fallback:
                    stats["first_fallback_step"] = len(st.order) + 1
                    stats["first_fallback_reason"] = reason
                fallback = True
                stats["fallback_task_count"] += 1
            s, f = placements[r]
            st.commit(i, r, s, f)
            if st.spent + st.raw_reserve > md.B:
                raise ArithmeticError("raw budget invariant violated")
        assignments = [{"task_id": md.tasks[i], "resource_id": md.resources[st.placements[i][0]],
                        "start_us": st.placements[i][1], "end_us": st.placements[i][2]}
                       for i in range(len(md.tasks))]
        stats["planned_assignments_sha256"] = sha256(canonical_json_bytes(assignments)).hexdigest()
        stats["internal_makespan_us"] = max(f for _, _, f in st.placements.values())
        stats["internal_compute_cost_ncu"] = st.spent
        return AlgorithmDecision(tuple(md.tasks[i] for i in st.order),
                                 {md.tasks[i]: md.resources[r] for i, (r, _, _) in st.placements.items()}, stats)


class ScoringControlScheduler(_ScoringBase):
    algorithm_id = "dcr_abl_scoring_control"
    algorithm_version = "dcr_abl_scoring_control_design_20261027_impl1"
    rank = "minimax"


class BDCScoreScheduler(_ScoringBase):
    algorithm_id = "dcr_abl_bdc_score"
    algorithm_version = "dcr_abl_bdc_score_design_20261027_impl1"
    rank = "bdc"
