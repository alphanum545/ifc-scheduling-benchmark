"""DCR-Min v2 and the calendar-based greedy baselines: constraint safety, polish never worse than the
search, determinism, and the policy calendar agreeing with the Dataset evaluator."""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "historical"))

from algorithms.dcr_ifc.model import Model  # noqa: E402
from algorithms.dcr_ifc_v4_rescue import DCRV4RescueScheduler  # noqa: E402
from algorithms.dcr_min import lower_bounds  # noqa: E402
from algorithms.dcr_min_v2 import Calendar, DCRMinV2CostScheduler, DCRMinV2MakespanScheduler  # noqa: E402
from algorithms.dcr_min_v2.scheduler import _indices  # noqa: E402
from algorithms.greedy_min import DeadlineLossCostScheduler, LOSS1MakespanScheduler  # noqa: E402
from generator.schedule import build_schedule  # noqa: E402
from test_dcr_v1 import random_input  # noqa: E402

CASES = range(40)


def _cost(md, dec):
    return sum(md.c[md.tasks.index(t)][md.resources.index(r)] for t, r in dec.resource_assignments.items())


def _eval_makespan(inp, dec):
    return build_schedule(inp.instance, task_order=list(dec.task_order),
                          resource_assignments=dict(dec.resource_assignments)).schedule["makespan_us"]


@pytest.mark.parametrize("case", range(60))
def test_calendar_matches_evaluator_on_perturbed_plans(case):
    inp = random_input(case)
    md = Model.create(inp)
    dec = DCRV4RescueScheduler().schedule(inp)
    order, assign = _indices(md, dec)
    cal, rng = Calendar(md, order), random.Random(case)
    for trial in range(5):
        a = list(assign)
        for _ in range(trial * 2):
            a[rng.randrange(len(a))] = rng.randrange(len(md.resources))
        got = cal.makespan(a)
        ev = build_schedule(inp.instance, task_order=list(dec.task_order),
                            resource_assignments={md.tasks[i]: md.resources[a[i]] for i in range(len(a))})
        assert got == ev.schedule["makespan_us"]


@pytest.mark.parametrize("case", CASES)
def test_v2_makespan_budget_safe_and_polish_never_worse(case):
    inp = random_input(case)
    md = Model.create(inp)
    for polish in (False, True):
        dec = DCRMinV2MakespanScheduler(polish=polish).schedule(inp)
        st = dec.internal_statistics
        if sum(md.cmin) > md.B:
            assert st["dcrmin_status"] == "budget_infeasible"
            continue
        assert _cost(md, dec) <= md.B
        assert st["internal_makespan_us"] == _eval_makespan(inp, dec)
        assert st["internal_makespan_us"] <= st["dcrmin_search_makespan_us"]
        assert st["internal_makespan_us"] >= lower_bounds(inp)["makespan_lb_us"]
        assert len(st["dcrmin_probes"]) <= DCRMinV2MakespanScheduler.max_probes


@pytest.mark.parametrize("case", CASES)
def test_v2_cost_meets_deadline_and_polish_never_worse(case):
    inp = random_input(case)
    md = Model.create(inp)
    for polish in (False, True):
        dec = DCRMinV2CostScheduler(polish=polish).schedule(inp)
        st = dec.internal_statistics
        assert len(st["dcrmin_probes"]) <= DCRMinV2CostScheduler.max_probes
        if st["dcrmin_status"] != "ok":
            assert st["dcrmin_status"] in ("deadline_not_met", "deadline_certified_infeasible")
            continue
        assert _eval_makespan(inp, dec) <= md.D
        assert _cost(md, dec) == st["internal_compute_cost_ncu"] <= st["dcrmin_search_cost_ncu"]


@pytest.mark.parametrize("case", CASES)
def test_greedy_baselines(case):
    inp = random_input(case)
    md = Model.create(inp)
    d = LOSS1MakespanScheduler().schedule(inp)
    if sum(md.cmin) <= md.B:
        assert _cost(md, d) <= md.B
    d = DeadlineLossCostScheduler().schedule(inp)
    st = d.internal_statistics
    assert st["internal_makespan_us"] == _eval_makespan(inp, d)
    if st["dloss_moves"]:
        assert st["internal_makespan_us"] <= md.D


@pytest.mark.parametrize("case", range(8))
def test_deterministic(case):
    inp = random_input(case)
    for cls in (DCRMinV2MakespanScheduler, DCRMinV2CostScheduler, LOSS1MakespanScheduler, DeadlineLossCostScheduler):
        a, b = cls().schedule(inp), cls().schedule(inp)
        assert a.task_order == b.task_order
        assert dict(a.resource_assignments) == dict(b.resource_assignments)


def test_seed_contract():
    for cls in (DCRMinV2MakespanScheduler, DCRMinV2CostScheduler, LOSS1MakespanScheduler, DeadlineLossCostScheduler):
        with pytest.raises(Exception):
            cls().schedule(random_input(0), seed=1)
