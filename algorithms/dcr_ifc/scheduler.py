"""Exact implementation of the 2026-09-07 DCR-IFC-v0 mathematical design."""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
from generator.canonical import canonical_json_bytes
from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from .model import Model
from .state import State
from .reserve import ReservePool

DESIGN_VERSION = "dcr_ifc_v0_design_20260907"
SPECIFICATION_SHA256 = "52d53eefa69bb97d2d4e7b75bad805a84cc3ff95c3277a669b381aa07cb122d9"


def loss(numerator: int, denominator: int) -> Fraction:
    if numerator < 0 or denominator < 0 or numerator > denominator:
        raise ArithmeticError("screened reserve loss is outside [0,1]")
    return Fraction(numerator, denominator) if denominator else Fraction(0)


class DCRScheduler:
    algorithm_id = "dcr_ifc_v0"
    algorithm_version = "dcr_ifc_v0_design_20260907_impl1"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR v0 is deterministic and accepts seed=None only")
        md = Model.create(scheduling_input)
        st = State(md)
        stats: dict[str, object] = {
            "design_version": DESIGN_VERSION, "specification_sha256": SPECIFICATION_SHA256,
            "novelty_status": "unverified", "admission_is_completion_certificate": False,
            "price_refresh_count": 0, "price_updates_per_refresh": 2, "price_vectors": 3,
            "checkpoint_count": len(md.theta), "candidate_count": 0,
            "reject_raw_budget": 0, "reject_current_domain_or_tail": 0,
            "reject_future_empty_domain": 0, "reject_child_arrival": 0,
            "reject_reserve_bound": 0, "screened_candidate_count": 0,
            "first_fallback_step": None, "first_fallback_reason": None,
            "fallback_task_count": 0, "full_schedule_rebuilds_inside_policy": 0,
            "input_budget_lower_bound_exceeds_budget": False,
            "largest_reserve_uplift_scaled_ncu": 0, "price_scale_H": md.H,
        }
        # The only true input-level monetary infeasibility claim.
        if st.raw_reserve > md.B:
            stats["input_budget_lower_bound_exceeds_budget"] = True
            mapping = {md.tasks[i]: md.resources[min(range(len(md.resources)),
                       key=lambda r: (md.c[i][r], md.p[i][r], r))] for i in md.topological}
            return AlgorithmDecision(tuple(md.tasks[i] for i in md.topological), mapping, stats)
        pool: ReservePool | None = None
        fallback = False
        while st.U:
            i = st.choose_task()
            placements = [st.insertion(i, r) for r in range(len(md.resources))]
            f0 = min(f for _, f in placements)
            budget_allowed = [r for r in range(len(md.resources)) if
                              st.spent + md.c[i][r] + st.raw_reserve - md.cmin[i] <= md.B]
            if not budget_allowed:
                raise ArithmeticError("raw budget invariant lost a cheapest-resource option")
            stats['candidate_count'] += len(md.resources)
            stats['reject_raw_budget'] += len(md.resources) - len(budget_allowed)
            screened = []
            reason = "empty_screen"
            if not fallback:
                if any(st.count[j] == 0 for j in st.U):
                    reason = "empty_current_domain"
                else:
                    if len(st.order) in md.epochs:
                        pool = ReservePool(st)
                        stats['price_refresh_count'] += 1
                    if pool is None:
                        raise ArithmeticError("uninitialized price pool")
                    pool.refresh_minima(st)
                    stats['largest_reserve_uplift_scaled_ncu'] = max(
                        stats['largest_reserve_uplift_scaled_ncu'], pool.current - pool.totals[0])
                    stime, sbudget = md.b[i] - f0, md.H * md.B - pool.current
                    if stime < 0:
                        reason = "negative_time_margin"
                    elif sbudget < 0:
                        reason = "current_reserve_exceeds_budget"
                    else:
                        for r in budget_allowed:
                            s, f = placements[r]
                            if not st.active[i][r] or f > md.b[i]:
                                stats['reject_current_domain_or_tail'] += 1
                                continue
                            deleted = st.capacity_deletions(i, r, s, f)
                            if deleted is None:
                                stats['reject_future_empty_domain'] += 1
                                continue
                            if not st.children_fit(i, r, s, f):
                                stats['reject_child_arrival'] += 1
                                continue
                            bound = pool.after_candidate(st, i, r, s, f, deleted)
                            if bound > md.H * md.B:
                                stats['reject_reserve_bound'] += 1
                                continue
                            pt, pb = loss(f - f0, stime), loss(bound - pool.current, sbudget)
                            screened.append(((max(pt, pb), min(pt, pb), f, md.c[i][r], r), r))
                        stats['screened_candidate_count'] += len(screened)
            if screened:
                r = min(screened)[1]
            else:
                r = min(budget_allowed, key=lambda q: (placements[q][1], md.c[i][q], q))
                if not fallback:
                    stats['first_fallback_step'] = len(st.order) + 1
                    stats['first_fallback_reason'] = reason
                fallback = True
                stats['fallback_task_count'] += 1
            s, f = placements[r]
            st.commit(i, r, s, f)
            if st.spent + st.raw_reserve > md.B:
                raise ArithmeticError("raw budget invariant violated")
        assignments = [{"task_id": md.tasks[i], "resource_id": md.resources[st.placements[i][0]],
                        "start_us": st.placements[i][1], "end_us": st.placements[i][2]}
                       for i in range(len(md.tasks))]
        stats['planned_assignments_sha256'] = sha256(canonical_json_bytes(assignments)).hexdigest()
        stats['internal_makespan_us'] = max(f for _, _, f in st.placements.values())
        stats['internal_compute_cost_ncu'] = st.spent
        return AlgorithmDecision(tuple(md.tasks[i] for i in st.order),
            {md.tasks[i]: md.resources[r] for i, (r, _, _) in st.placements.items()}, stats)
