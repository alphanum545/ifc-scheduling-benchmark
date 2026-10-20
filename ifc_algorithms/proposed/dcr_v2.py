"""DCR-v2 candidates: same-complexity changes confined to the champion's empty-screen state.

Hypotheses, decision rules and the complexity ledger are predeclared in
docs/superpowers/specs/2026-09-30-dcr-v2-fallback-design.md.

The per-step loop mirrors the accepted champion `DCRV1AdmissionScheduler.schedule`
(.local/algorithm_source/algorithms/dcr_ifc_v1/scheduler.py) statement for statement.
Only the branch taken when no candidate is admitted differs, so any run on which the
champion never reaches that branch yields byte-identical decisions (tested).

Requires `.local/algorithm_source` and `.local/Dataset` on sys.path (scripts/local_lab.py
and tests/algorithms/conftest.py arrange this). The champion's Model, State and
ReservePool are reused unmodified; no price vector, refresh epoch or rebuild is added.
"""
from __future__ import annotations

from hashlib import sha256

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from algorithms.dcr_ifc.model import Model
from algorithms.dcr_ifc_optimized.state import State
from algorithms.dcr_ifc_v1.reserve import ReservePool
from algorithms.dcr_ifc_v1.scheduler import loss
from generator.canonical import canonical_json_bytes

from .dcr_v2_rules import champion_fallback_choice, relaxed_choice, sparing_fallback_choice

DESIGN_VERSION = "dcr_ifc_v2_fallback_design_20260930"


class DeadlineCertainlyLost(Exception):
    """Raised (only when opted in) once a policy's own plan provably misses the deadline.

    A committed finish f > b[i] = D - h[i] implies makespan >= f + h[i] > D, because
    every descendant chain needs at least its fastest execution time and transfers and
    waits are non-negative. Deliberately not an ArithmeticError/ValueError.
    """

    def __init__(self, step: int) -> None:
        super().__init__(f"deadline certainly lost at step {step}")
        self.step = step


class _DCRV2Base:
    algorithm_id = "dcr_ifc_v2_base"
    algorithm_version = "dcr_ifc_v2_base_design_20260930_impl1"
    # Candidate A: relax only the priced reserve bound, one step at a time (non-sticky).
    graded_relaxation = False
    # Candidate B: cheapest timely resource inside the (still sticky) fallback.
    sparing_fallback = False
    # Portfolio members only: stop as soon as the plan provably misses the deadline.
    abort_when_deadline_lost = False

    def _filter_admitted(self, st, i, screened, stats):
        """Hook over the champion-admitted candidates of one step; identity here.

        Overrides must return a non-empty subset in O(len(screened)) so that the
        champion ranking and fallback semantics are otherwise untouched.
        """
        return screened

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR v2 is deterministic and accepts seed=None only")
        md = Model.create(scheduling_input)
        st = State(md)
        m = len(md.resources)
        HB = md.H * md.B
        stats: dict[str, object] = {
            "design_version": DESIGN_VERSION, "novelty_status": "unverified",
            "baseline_lineage": "dcr_ifc_v1_arrival_design_20260907_admission1",
            "corrected_ranking": False, "graded_relaxation": self.graded_relaxation,
            "sparing_fallback": self.sparing_fallback,
            "arrival_reserve_reject_count": 0, "largest_arrival_correction_scaled_ncu": 0,
            "admission_is_completion_certificate": False,
            "price_refresh_count": 0, "price_updates_per_refresh": 2, "price_vectors": 3,
            "checkpoint_count": len(md.theta), "candidate_count": 0,
            "reject_raw_budget": 0, "reject_current_domain_or_tail": 0,
            "reject_future_empty_domain": 0, "reject_child_arrival": 0,
            "reject_reserve_bound": 0, "screened_candidate_count": 0,
            "screened_step_count": 0, "capacity_deletions_calls": 0,
            "price_refresh_steps": [], "reserve_exceeded_screened_steps": 0,
            "relaxed_step_count": 0, "first_relaxed_step": None,
            "first_empty_screen_breakdown": None,
            "first_fallback_step": None, "first_fallback_reason": None,
            "fallback_task_count": 0, "full_schedule_rebuilds_inside_policy": 0,
            "input_budget_lower_bound_exceeds_budget": False,
            "largest_reserve_uplift_scaled_ncu": 0, "price_scale_H": md.H,
        }
        # Same input-level monetary infeasibility shortcut as the champion.
        if st.raw_reserve > md.B:
            stats["input_budget_lower_bound_exceeds_budget"] = True
            mapping = {md.tasks[i]: md.resources[min(range(m),
                       key=lambda r: (md.c[i][r], md.p[i][r], r))] for i in md.topological}
            return AlgorithmDecision(tuple(md.tasks[i] for i in md.topological), mapping, stats)
        pool: ReservePool | None = None
        fallback = False
        while st.U:
            step = len(st.order) + 1
            i = st.choose_task()
            placements = [st.insertion(i, r) for r in range(m)]
            f0 = min(f for _, f in placements)
            budget_allowed = [r for r in range(m) if
                              st.spent + md.c[i][r] + st.raw_reserve - md.cmin[i] <= md.B]
            if not budget_allowed:
                raise ArithmeticError("raw budget invariant lost a cheapest-resource option")
            stats['candidate_count'] += m
            stats['reject_raw_budget'] += m - len(budget_allowed)
            screened = []
            relaxed: list[tuple[int, int, int, int]] = []   # (bound, finish, cost, r)
            local = {"tail_or_domain": 0, "future_empty_domain": 0, "child_arrival": 0}
            reserve_exceeded = False
            reason = "empty_screen"
            if not fallback:
                if any(st.count[j] == 0 for j in st.U):
                    reason = "empty_current_domain"
                else:
                    if len(st.order) in md.epochs:
                        pool = ReservePool(st)
                        stats['price_refresh_count'] += 1
                        stats['price_refresh_steps'].append(step)
                    if pool is None:
                        raise ArithmeticError("uninitialized price pool")
                    pool.refresh_minima(st)
                    stats['largest_reserve_uplift_scaled_ncu'] = max(
                        stats['largest_reserve_uplift_scaled_ncu'], pool.current - pool.totals[0])
                    stime, sbudget = md.b[i] - f0, HB - pool.current
                    reserve_exceeded = sbudget < 0
                    if stime < 0:
                        reason = "negative_time_margin"
                    elif reserve_exceeded and not self.graded_relaxation:
                        reason = "current_reserve_exceeds_budget"
                    else:
                        # With sbudget < 0 every bound >= current > H*B, so every surviving
                        # candidate is relaxed and loss() is never reached (monotonicity is
                        # asserted inside candidate_bounds).
                        stats['screened_step_count'] += 1
                        if reserve_exceeded:
                            stats['reserve_exceeded_screened_steps'] += 1
                        candidates = {}
                        for r in budget_allowed:
                            s, f = placements[r]
                            if not st.active[i][r] or f > md.b[i]:
                                stats['reject_current_domain_or_tail'] += 1
                                local['tail_or_domain'] += 1
                                continue
                            stats['capacity_deletions_calls'] += 1
                            deleted = st.capacity_deletions(i, r, s, f)
                            if deleted is None:
                                stats['reject_future_empty_domain'] += 1
                                local['future_empty_domain'] += 1
                                continue
                            candidates[r] = deleted
                        pool.prepare(st, i, placements, candidates)
                        for r, deleted in candidates.items():
                            s, f = placements[r]
                            bounds = pool.candidate_bounds(st, i, r, s, f, deleted)
                            if bounds is None:
                                stats['reject_child_arrival'] += 1
                                local['child_arrival'] += 1
                                continue
                            capacity_bound, bound = bounds
                            stats['largest_arrival_correction_scaled_ncu'] = max(
                                stats['largest_arrival_correction_scaled_ncu'], bound - capacity_bound)
                            if capacity_bound <= HB < bound:
                                stats['arrival_reserve_reject_count'] += 1
                            if bound > HB:
                                stats['reject_reserve_bound'] += 1
                                relaxed.append((bound, f, md.c[i][r], r))
                                continue
                            pt, pb = loss(f - f0, stime), loss(capacity_bound - pool.current, sbudget)
                            screened.append(((max(pt, pb), min(pt, pb), f, md.c[i][r], r), r))
                        stats['screened_candidate_count'] += len(screened)
                        if screened:
                            screened = self._filter_admitted(st, i, screened, stats)
            if screened:
                r = min(screened)[1]
            else:
                if not fallback and stats['first_empty_screen_breakdown'] is None:
                    stats['first_empty_screen_breakdown'] = {
                        "step": step, "reason": reason, "budget_allowed": len(budget_allowed),
                        "current_reserve_exceeds_budget": reserve_exceeded,
                        **local, "reserve_only_candidates": len(relaxed),
                    }
                pick = relaxed_choice(relaxed) if self.graded_relaxation else None
                if pick is not None:
                    r = pick
                    stats['relaxed_step_count'] += 1
                    if stats['first_relaxed_step'] is None:
                        stats['first_relaxed_step'] = step
                else:
                    finish = [f for _, f in placements]
                    if self.sparing_fallback:
                        r = sparing_fallback_choice(budget_allowed, finish, md.c[i], latest_finish=md.b[i])
                    else:
                        r = champion_fallback_choice(budget_allowed, finish, md.c[i])
                    if not fallback:
                        stats['first_fallback_step'] = step
                        stats['first_fallback_reason'] = reason
                    fallback = True
                    stats['fallback_task_count'] += 1
            s, f = placements[r]
            st.commit(i, r, s, f)
            if st.spent + st.raw_reserve > md.B:
                raise ArithmeticError("raw budget invariant violated")
            if self.abort_when_deadline_lost and f > md.b[i]:
                raise DeadlineCertainlyLost(step)
        assignments = [{"task_id": md.tasks[i], "resource_id": md.resources[st.placements[i][0]],
                        "start_us": st.placements[i][1], "end_us": st.placements[i][2]}
                       for i in range(len(md.tasks))]
        stats['planned_assignments_sha256'] = sha256(canonical_json_bytes(assignments)).hexdigest()
        stats['internal_makespan_us'] = max(f for _, _, f in st.placements.values())
        stats['internal_compute_cost_ncu'] = st.spent
        return AlgorithmDecision(tuple(md.tasks[i] for i in st.order),
            {md.tasks[i]: md.resources[r] for i, (r, _, _) in st.placements.items()}, stats)


class DCRV2GradedScheduler(_DCRV2Base):
    """Candidate A: graded, non-sticky relaxation of the priced reserve bound only."""
    algorithm_id = "dcr_ifc_v2_graded"
    algorithm_version = "dcr_ifc_v2_graded_design_20260930_impl1"
    graded_relaxation = True


class DCRV2SparingScheduler(_DCRV2Base):
    """Candidate B: champion trigger, cheapest-timely choice inside the sticky fallback."""
    algorithm_id = "dcr_ifc_v2_sparing"
    algorithm_version = "dcr_ifc_v2_sparing_design_20260930_impl1"
    sparing_fallback = True
