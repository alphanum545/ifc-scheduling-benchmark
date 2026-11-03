"""DCR-Min: DCR used as an unchanged oracle inside a bounded search, for the two
single-objective variants of the joint deadline/budget problem.

  DCRMinMakespanScheduler   minimise makespan     subject to compute cost <= B  (D is ignored)
  DCRMinCostScheduler       minimise compute cost subject to makespan <= D      (B is ignored)

No policy, rule or parameter of DCR is changed. The oracle is run with a probed deadline
(resp. budget), and its own insertion-calendar plan is read back from `internal_makespan_us` /
`internal_compute_cost_ncu`, exactly as DCR-v4R's self-check does. Nothing here calls the
Dataset evaluator.

Start plans
-----------
Makespan under budget: every DCR run keeps the raw cheapest-remaining budget invariant, so
EVERY probe is budget-feasible when sum_i cmin_i <= B. Start probes: target LB_T (DCR falls
back to its budget-safe earliest-finish rule) and target 2 * that makespan (slack, so DCR's
reserve admission is active). Cost under deadline: start probes at budget LB_C(D) (the plan is
cost-optimal if it meets D) and at the all-expensive budget sum_i cmax_i. Only plans meeting D
count; if none does, the fastest plan is returned and flagged.

Search (strategy), on the target t, with incumbent value `best`
-----------------------------------------------------------------
  bisect   lo = lower bound; mid = (lo + best) / 2; a probe that hits (value <= mid and the
           hard constraint holds) lowers best, otherwise lo = mid.
  descent  t = best * (1 - delta), delta = 1/8; improvement -> delta = min(2 delta, 1/4),
           otherwise delta /= 2; stop at delta < 1/256.
  hybrid   bisect with 2/3 of the probe budget, then descent from the incumbent.

DCR is not monotone in D or B (meeting D does not imply meeting a larger D), so bisection
can step into failing regions and descent can stall on a local step; the hybrid uses the
bracket first and then searches next to the frontier, where DCR is strongest.

Lower bounds reported in the statistics (valid for any schedule; zero communication):
    LB_T    = max( max_i (a_i + pmin_i + h_i),  ceil(sum_i pmin_i / m) )
    LB_C(D) = sum_i min{ c_ir : a_i + p_ir + h_i <= D }   (None if some task cannot meet D)

Defaults (chosen on a 35-instance tuning grid of dev instances with <= 200 tasks; oracle x
strategy = {DCR-v1 Admission, DCR-v4, DCR-v4R} x {bisect, descent, hybrid}): oracle DCR-v4R,
descent for makespan, bisect for cost, 12 probes. See docs/proposed/DCR_MIN.md.

The result is "best found", not a certified optimum. Cost: at most `max_probes` oracle runs.
"""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput
from algorithms.dcr_ifc.model import Model
from algorithms.dcr_ifc_v4_rescue import DCRV4RescueScheduler

DESIGN_VERSION = "dcr_min_search_design_20261103"


def lower_bounds(inp: AlgorithmInput) -> dict[str, int | None]:
    md = Model.create(inp)
    n, m = len(md.tasks), len(md.resources)
    cp = max(md.a[i] + md.pmin[i] + md.h[i] for i in range(n))
    work = -(-sum(md.pmin) // m)
    # In ANY schedule, task i on resource r forces makespan >= a_i + p_ir + h_i, so only such
    # resources can host i in a deadline-feasible schedule.
    per_task = [[md.c[i][r] for r in range(m) if md.a[i] + md.p[i][r] + md.h[i] <= md.D] for i in range(n)]
    return {
        "makespan_lb_us": max(cp, work),
        "cost_lb_ncu": sum(md.cmin),
        "cost_lb_deadline_ncu": None if any(not row for row in per_task) else sum(min(row) for row in per_task),
        "cost_max_ncu": sum(max(row) for row in md.c),
    }


class _Search:
    algorithm_id = "dcr_min_base"
    algorithm_version = "dcr_min_base_impl1"
    strategy = "hybrid"
    max_probes = 12
    delta0, delta_max, delta_min = Fraction(1, 8), Fraction(1, 4), Fraction(1, 256)
    bisect_tol = Fraction(1, 200)

    def __init__(self, oracle=None, *, strategy: str | None = None, max_probes: int | None = None) -> None:
        self.oracle = oracle if oracle is not None else DCRV4RescueScheduler()
        if strategy is not None:
            self.strategy = strategy
        if max_probes is not None:
            self.max_probes = max_probes
        if self.strategy not in ("bisect", "descent", "hybrid"):
            raise ValueError(self.strategy)

    def _probe(self, inp: AlgorithmInput, log: list, **override):
        dec = self.oracle.schedule(replace(inp, **override))
        st = dec.internal_statistics
        ms, cost = st.get("internal_makespan_us"), st.get("internal_compute_cost_ncu")
        log.append({**override, "makespan_us": ms, "cost_ncu": cost})
        return dec, ms, cost

    def _search(self, lo: int, best_value, run, log: list) -> None:
        """`run(target)` probes once and returns (improved, hit)."""
        if self.strategy in ("bisect", "hybrid"):
            limit = self.max_probes if self.strategy == "bisect" else max(len(log), (2 * self.max_probes) // 3)
            while len(log) < limit:
                hi = best_value()
                if hi - lo <= max(1, hi * self.bisect_tol):
                    break
                mid = (lo + hi) // 2
                _, hit = run(mid)
                if not hit:
                    lo = mid
        if self.strategy in ("descent", "hybrid"):
            delta = self.delta0
            while len(log) < self.max_probes and delta >= self.delta_min:
                target = max(1, int(best_value() * (1 - delta)))
                if target <= lo and self.strategy == "hybrid":
                    break
                improved, _ = run(target)
                delta = min(2 * delta, self.delta_max) if improved else delta / 2

    def _finish(self, dec: AlgorithmDecision, extra: dict) -> AlgorithmDecision:
        stats = dict(dec.internal_statistics)
        stats.update({"dcrmin_design_version": DESIGN_VERSION, "dcrmin_oracle": self.oracle.algorithm_id,
                      "dcrmin_strategy": self.strategy, **{f"dcrmin_{k}": v for k, v in extra.items()}})
        return AlgorithmDecision(dec.task_order, dict(dec.resource_assignments), stats)


class DCRMinMakespanScheduler(_Search):
    """Minimise makespan subject to the budget; the instance deadline is not used."""
    algorithm_id = "dcr_min_makespan"
    algorithm_version = "dcr_min_makespan_design_20261103_impl1"
    strategy = "descent"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR-Min is deterministic and accepts seed=None only")
        B = scheduling_input.budget_ncu
        lb = lower_bounds(scheduling_input)
        log: list = []
        if lb["cost_lb_ncu"] > B:  # no schedule can meet the budget
            dec, _, _ = self._probe(scheduling_input, log, deadline_us=lb["makespan_lb_us"])
            return self._finish(dec, {**lb, "probes": log, "status": "budget_infeasible"})
        best: list = []  # [makespan, cost, decision]

        def run(deadline: int):
            dec, ms, cost = self._probe(scheduling_input, log, deadline_us=deadline)
            ok = ms is not None and cost is not None and cost <= B
            improved = ok and (not best or (ms, cost) < tuple(best[:2]))
            if improved:
                best[:] = [ms, cost, dec]
            return improved, ok and ms <= deadline

        run(lb["makespan_lb_us"])                 # budget-safe earliest-finish fallback plan
        if not best:  # unreachable while DCR's raw budget invariant holds; kept as a guard
            dec, _, _ = self._probe(scheduling_input, log)
            return self._finish(dec, {**lb, "probes": log, "status": "no_budget_feasible_probe"})
        run(2 * best[0])                           # slack target: reserve admission active
        self._search(lb["makespan_lb_us"], lambda: best[0], run, log)
        return self._finish(best[2], {**lb, "probes": log, "status": "ok", "best_makespan_us": best[0]})


class DCRMinCostScheduler(_Search):
    """Minimise compute cost subject to the deadline; the instance budget is not used."""
    algorithm_id = "dcr_min_cost"
    algorithm_version = "dcr_min_cost_design_20261103_impl1"
    strategy = "bisect"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DCR-Min is deterministic and accepts seed=None only")
        D = scheduling_input.deadline_us
        lb = lower_bounds(scheduling_input)
        log: list = []
        best: list = []      # [cost, makespan, decision] among plans meeting D
        fastest: list = []   # [makespan, cost, decision] in case none meets D

        def run(budget: int):
            dec, ms, cost = self._probe(scheduling_input, log, budget_ncu=budget)
            if ms is None or cost is None:
                return False, False
            if not fastest or (ms, cost) < tuple(fastest[:2]):
                fastest[:] = [ms, cost, dec]
            improved = ms <= D and (not best or (cost, ms) < tuple(best[:2]))
            if improved:
                best[:] = [cost, ms, dec]
            return improved, ms <= D and cost <= budget

        if lb["cost_lb_deadline_ncu"] is None:     # some task cannot finish by D anywhere
            run(lb["cost_max_ncu"])
            return self._finish(fastest[2], {**lb, "probes": log, "status": "deadline_certified_infeasible"})
        if run(lb["cost_lb_deadline_ncu"])[0]:
            return self._finish(best[2], {**lb, "probes": log, "status": "optimal_at_cost_lb",
                                          "best_cost_ncu": best[0]})
        run(lb["cost_max_ncu"])
        if not best:
            return self._finish(fastest[2], {**lb, "probes": log, "status": "deadline_not_met"})
        self._search(lb["cost_lb_deadline_ncu"], lambda: best[0], run, log)
        return self._finish(best[2], {**lb, "probes": log, "status": "ok", "best_cost_ncu": best[0]})
