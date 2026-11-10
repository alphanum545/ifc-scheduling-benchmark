"""DCR-Cost (paper 2: minimize compute cost subject to the deadline).

Checked on random instances against the pinned Dataset evaluator (generator.schedule.build_schedule):
  * the schedulers' internal makespan and cost equal the evaluator's (the _Simulator and the priced list
    scheduler are exact replicas of its timing);
  * dominance: v2 never costs more than v1, v3 never costs more than v2, and each meets D whenever its
    predecessor does;
  * the improvement passes only lower cost and keep the deadline;
  * the prefix-resume simulation equals a full rebuild;
  * determinism, seed rejection, and independence from the budget.
"""
from __future__ import annotations

import dataclasses
import random
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "historical"))

from generator.schedule import build_schedule, evaluate_schedule  # noqa: E402
from algorithms.common.interface import AlgorithmContractError  # noqa: E402
from algorithms.dcr_cost import DCRCostImprovedScheduler, DCRCostSplitScheduler  # noqa: E402
from algorithms.dcr_cost.scheduler import _Simulator, improve  # noqa: E402
from algorithms.dcr_cost_v3 import DCRCostPricedScheduler, deep_improve, priced_plan  # noqa: E402
from algorithms.dcr_cost_v3.scheduler import K_GRID, MODES  # noqa: E402
from algorithms.dcr_ifc.model import Model  # noqa: E402
from test_dcr_v1 import random_input  # noqa: E402

CASES = range(60)
_CACHE: dict = {}


def run(cls, case):
    """(input, decision, evaluator result), computed once per scheduler class and case."""
    key = (cls.__name__, case)
    if key not in _CACHE:
        inp = random_input(case)
        d = cls().schedule(inp)
        ev = build_schedule(inp.instance, task_order=d.task_order, resource_assignments=d.resource_assignments,
                            deadline_us=inp.deadline_us, budget_ncu=inp.budget_ncu)
        _CACHE[key] = (inp, d, ev)
    return _CACHE[key]


def indexed(md, decision):
    it = {t: i for i, t in enumerate(md.tasks)}
    ir = {r: q for q, r in enumerate(md.resources)}
    order = [it[t] for t in decision.task_order]
    assign = [ir[decision.resource_assignments[md.tasks[i]]] for i in range(len(md.tasks))]
    return order, assign


@pytest.mark.parametrize("cls", [DCRCostImprovedScheduler, DCRCostSplitScheduler, DCRCostPricedScheduler])
@pytest.mark.parametrize("case", CASES)
def test_decision_is_complete_and_internal_metrics_equal_the_evaluator(cls, case):
    inp, d, ev = run(cls, case)
    md = Model.create(inp)
    assert sorted(d.task_order) == sorted(md.tasks)
    assert set(d.resource_assignments) == set(md.tasks)
    assert set(d.resource_assignments.values()) <= set(md.resources)
    check = evaluate_schedule(inp.instance, ev.schedule, deadline_us=inp.deadline_us, budget_ncu=inp.budget_ncu)
    assert check.schedule["makespan_us"] == ev.schedule["makespan_us"]
    assert d.internal_statistics["internal_compute_cost_ncu"] == ev.schedule["compute_cost_ncu"]
    if cls is not DCRCostImprovedScheduler:  # v1 reports the makespan of the plan before improvement
        assert d.internal_statistics["internal_makespan_us"] == ev.schedule["makespan_us"]


@pytest.mark.parametrize("case", CASES)
def test_dominance_v1_v2_v3(case):
    _, _, e1 = run(DCRCostImprovedScheduler, case)
    _, _, e2 = run(DCRCostSplitScheduler, case)
    inp, d3, e3 = run(DCRCostPricedScheduler, case)
    if e1.deadline_feasible:
        assert e2.deadline_feasible
        assert e2.schedule["compute_cost_ncu"] <= e1.schedule["compute_cost_ncu"]
    if e2.deadline_feasible:
        assert e3.deadline_feasible
        assert e3.schedule["compute_cost_ncu"] <= e2.schedule["compute_cost_ncu"]
    s = d3.internal_statistics
    assert s["v2_compute_cost_ncu"] == e2.schedule["compute_cost_ncu"]
    assert s["v2_meets_deadline"] == e2.deadline_feasible


@pytest.mark.parametrize("case", range(20))
def test_v3_is_deterministic_and_ignores_the_budget(case):
    inp, d, _ = run(DCRCostPricedScheduler, case)
    again = DCRCostPricedScheduler().schedule(inp)
    other_budget = DCRCostPricedScheduler().schedule(dataclasses.replace(inp, budget_ncu=inp.budget_ncu * 3 + 7))
    for x in (again, other_budget):
        assert x.task_order == d.task_order
        assert dict(x.resource_assignments) == dict(d.resource_assignments)


def test_seed_is_rejected():
    inp = random_input(0)
    for cls in (DCRCostImprovedScheduler, DCRCostSplitScheduler, DCRCostPricedScheduler):
        with pytest.raises(AlgorithmContractError):
            cls().schedule(inp, seed=1)


@pytest.mark.parametrize("case", CASES)
def test_priced_plan_timing_equals_the_evaluator(case):
    inp = random_input(case)
    md = Model.create(inp)
    tables = _Simulator(md, list(md.topological))
    scale = Fraction(sum(max(r) - min(r) for r in md.c), md.D)
    for mode in MODES:
        for k in (K_GRID[0], -3, 0, 3, K_GRID[-1]):
            mu = scale * Fraction(2) ** k
            order, assign, ms = priced_plan(md, tables, mu.numerator, mu.denominator, mode)
            assert sorted(order) == list(range(len(md.tasks)))
            ev = build_schedule(inp.instance, task_order=[md.tasks[i] for i in order],
                                resource_assignments={md.tasks[i]: md.resources[assign[i]] for i in range(len(order))},
                                deadline_us=inp.deadline_us, budget_ncu=inp.budget_ncu)
            assert ev.schedule["makespan_us"] == ms
            assert _Simulator(md, order).makespan(assign) == ms


def test_priced_plan_rejects_an_unknown_mode():
    md = Model.create(random_input(0))
    with pytest.raises(ValueError):
        priced_plan(md, _Simulator(md, list(md.topological)), 1, 1, "other")


@pytest.mark.parametrize("case", CASES)
def test_improvement_passes_lower_cost_and_keep_the_deadline(case):
    inp, d, ev = run(DCRCostSplitScheduler, case)
    md = Model.create(inp)
    order, assign = indexed(md, d)
    cost = lambda a: sum(md.c[i][a[i]] for i in range(len(a)))  # noqa: E731
    sim = _Simulator(md, order)
    for fn in (improve, deep_improve):
        new, stats = fn(md, order, assign)
        if sim.makespan(assign) > md.D:
            assert new == assign  # a plan that misses D is returned unchanged
            continue
        assert sim.makespan(new) <= md.D
        assert cost(new) <= cost(assign)
        saving = stats.get("improve_saving_ncu", stats.get("deep_saving_ncu"))
        assert cost(assign) - cost(new) == saving
    # deep_improve ends in a local optimum of its own move when the rebuild budget was not exhausted
    new, stats = deep_improve(md, order, assign, tries=len(md.resources), rebuilds_per_task=10 ** 6)
    if sim.makespan(assign) <= md.D:
        for i in range(len(new)):
            for q in range(len(md.resources)):
                if md.c[i][q] < md.c[i][new[i]]:
                    trial = list(new)
                    trial[i] = q
                    assert sim.makespan(trial) > md.D


@pytest.mark.parametrize("case", range(30))
def test_prefix_resume_equals_a_full_rebuild(case):
    inp, d, _ = run(DCRCostSplitScheduler, case)
    md = Model.create(inp)
    order, assign = indexed(md, d)
    sim = _Simulator(md, order)
    full = sim.run(assign)
    rng = random.Random(case)
    for _ in range(10):
        i = rng.randrange(len(assign))
        changed = list(assign)
        changed[i] = rng.randrange(len(md.resources))
        resumed = sim.run(changed, k=sim.pos[i], base=full[1:])
        rebuilt = sim.run(changed)
        assert resumed[0] == rebuilt[0]
        assert resumed[1] == rebuilt[1]
        assert resumed[2] == rebuilt[2]
