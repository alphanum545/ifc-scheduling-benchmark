"""Predeclared component ablations of DCR-v1 Admission (paper 1).

Every variant is the DCR-v1 Admission step loop (algorithms/dcr_ifc_v1/scheduler.py,
DCRV1AdmissionScheduler) with exactly ONE component changed. The v1 sources are imported,
never edited, so their hashes and replay references are untouched.

Components of DCR-v1 Admission:
  (R) priced reserve admission: a candidate is admitted only if the deadline- and
      capacity-aware dual-priced lower bound on the remaining cost (with the exact
      child-arrival correction) fits the budget;
  (P) three fixed dual price vectors (capacity checkpoints) inside that bound;
  (M) parameter-free minimax ranking of admitted candidates by
      (max(time_loss, budget_loss), min(...), finish, cost, resource).
Always kept, because they are safety or time-feasibility mechanics rather than the
contribution: the raw cheapest-remaining budget invariant, the latest-finish and
domain/capacity time screens, the task priority, and the budget-safe fallback.

Variants (IDs in algorithms.toml):
  control        all components; must reproduce DCR-v1 Admission decisions exactly
  no-reserve     (R) removed: admission and budget loss use only the raw cheapest-
                 remaining reserve, i.e. the classic prior-art reserve
  zero-prices    (P) removed: one zero price vector (bound = sum of cheapest timely
                 options, no capacity pricing), used three times
  time-rank      (M) replaced by time loss only
  budget-rank    (M) replaced by budget loss only
  weighted-rank  (M) replaced by the weighted sum 0.5*time_loss + 0.5*budget_loss
Ties after the replaced primary key fall back to (finish, cost, resource), as in v1.
No parameter is fitted; the 0.5 weight is the conventional default of the weighted
comparators (BDC/BDDC omega, BDHEFT alpha).
"""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256

from generator.canonical import canonical_json_bytes
from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from algorithms.dcr_ifc.model import Model
from algorithms.dcr_ifc.reserve import dot
from algorithms.dcr_ifc.state import MonotoneChoices
from algorithms.dcr_ifc_optimized.state import State
from algorithms.dcr_ifc_v1.reserve import ReservePool
from algorithms.dcr_ifc_v1.scheduler import loss

DESIGN_VERSION = "dcr_ablations_paper1_design_20261024"


class ZeroPricePool(ReservePool):
    """Same pool and child-arrival sweep, but all three price vectors are zero."""

    def __init__(self, state) -> None:
        super().__init__(state)
        md = state.model
        m, k = len(md.resources), len(md.theta)
        zero = [[0] * k for _ in range(m)]
        weights = {j: [md.H * md.c[j][r] for r in range(m)] for j in state.U}
        orders = {j: sorted((r for r in range(m) if state.active[j][r]),
                            key=lambda r: (weights[j][r], md.p[j][r], r)) for j in state.U}
        if any(not order for order in orders.values()):
            raise ValueError("cannot price an empty resource domain")
        self.prices = [zero, zero, zero]
        self.weights = [weights, weights, weights]
        self.choices = [{j: MonotoneChoices(o) for j, o in orders.items()} for _ in range(3)]


class _AblationBase:
    algorithm_id = "dcr_abl_base"
    algorithm_version = "dcr_abl_base_design_20261024_impl1"
    priced_reserve = True
    pool_class = ReservePool
    rank = "minimax"  # minimax | time | budget | sum

    def _key(self, pt: Fraction, pb: Fraction, f: int, cost: int, r: int) -> tuple:
        if self.rank == "minimax":
            return (max(pt, pb), min(pt, pb), f, cost, r)
        if self.rank == "time":
            return (pt, f, cost, r)
        if self.rank == "budget":
            return (pb, f, cost, r)
        if self.rank == "sum":
            return ((pt + pb) / 2, f, cost, r)
        raise ValueError(self.rank)

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR ablations are deterministic and accept seed=None only")
        md = Model.create(scheduling_input)
        st = State(md)
        m = len(md.resources)
        HB = md.H * md.B
        stats: dict[str, object] = {
            "design_version": DESIGN_VERSION, "baseline_lineage": "dcr_ifc_v1_arrival_design_20260907_admission1",
            "priced_reserve": self.priced_reserve, "pool": self.pool_class.__name__, "rank": self.rank,
            "candidate_count": 0, "screened_candidate_count": 0, "reject_reserve_bound": 0,
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
                elif self.priced_reserve:
                    if len(st.order) in md.epochs:
                        pool = self.pool_class(st)
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
                        for r, deleted in candidates.items():
                            s, f = placements[r]
                            bounds = pool.candidate_bounds(st, i, r, s, f, deleted)
                            if bounds is None:
                                continue
                            capacity_bound, bound = bounds
                            if bound > HB:
                                stats["reject_reserve_bound"] += 1
                                continue
                            # Admission variant: corrected bound admits, capacity bound ranks.
                            pt, pb = loss(f - f0, stime), loss(capacity_bound - pool.current, sbudget)
                            screened.append((self._key(pt, pb, f, md.c[i][r], r), r))
                else:
                    # Raw cheapest-remaining reserve only (no priced bound, no child sweep).
                    stime = md.b[i] - f0
                    sbudget = md.B - st.spent - st.raw_reserve
                    if stime < 0:
                        reason = "negative_time_margin"
                    else:
                        for r in budget_allowed:
                            s, f = placements[r]
                            if not st.active[i][r] or f > md.b[i]:
                                continue
                            if st.capacity_deletions(i, r, s, f) is None:
                                continue
                            pt = loss(f - f0, stime)
                            pb = loss(md.c[i][r] - md.cmin[i], sbudget)
                            screened.append((self._key(pt, pb, f, md.c[i][r], r), r))
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


def _variant(name: str, **attrs) -> type:
    ident = f"dcr_abl_{name.replace('-', '_')}"
    return type(f"DCRAblation_{name.replace('-', '_')}", (_AblationBase,),
                {"algorithm_id": ident, "algorithm_version": f"{ident}_design_20261024_impl1", **attrs})


ControlScheduler = _variant("control")
NoReserveScheduler = _variant("no-reserve", priced_reserve=False)
ZeroPricesScheduler = _variant("zero-prices", pool_class=ZeroPricePool)
TimeRankScheduler = _variant("time-rank", rank="time")
BudgetRankScheduler = _variant("budget-rank", rank="budget")
WeightedRankScheduler = _variant("weighted-rank", rank="sum")
