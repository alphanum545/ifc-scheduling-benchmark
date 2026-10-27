"""DCR-v4R must return DCR-v4's decision when v4's plan is feasible, otherwise DCR-v3's feasible
plan when there is one, otherwise DCR-v4's decision; it must stay budget-safe."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "historical"))

from algorithms.dcr_ifc.model import Model  # noqa: E402
from algorithms.dcr_ifc_v4 import DCRV4QualityScheduler  # noqa: E402
from ifc_algorithms.proposed.dcr_v2_rules import plan_is_jointly_feasible  # noqa: E402
from ifc_algorithms.proposed.dcr_v3_rescue import DCRV3RescueScheduler  # noqa: E402
from algorithms.dcr_ifc_v4_rescue import DCRV4RescueScheduler  # noqa: E402
from test_dcr_v1 import random_input  # noqa: E402

CASES = range(150)


@pytest.mark.parametrize("case", CASES)
def test_v4r_composition_rule(case):
    inp = random_input(case)
    D, B = inp.deadline_us, inp.budget_ncu
    v4 = DCRV4QualityScheduler().schedule(inp)
    got = DCRV4RescueScheduler().schedule(inp)
    v4_ok = plan_is_jointly_feasible(v4.internal_statistics, deadline_us=D, budget_ncu=B)
    if v4_ok or v4.internal_statistics.get("input_budget_lower_bound_exceeds_budget"):
        expected = v4
    else:
        v3 = DCRV3RescueScheduler().schedule(inp)
        expected = v3 if plan_is_jointly_feasible(v3.internal_statistics, deadline_us=D, budget_ncu=B) else v4
    assert got.task_order == expected.task_order
    assert dict(got.resource_assignments) == dict(expected.resource_assignments)


@pytest.mark.parametrize("case", CASES)
def test_v4r_never_loses_a_v4_or_v3_plan_and_is_budget_safe(case):
    inp = random_input(case)
    D, B = inp.deadline_us, inp.budget_ncu
    got = DCRV4RescueScheduler().schedule(inp)
    ok = lambda d: plan_is_jointly_feasible(d.internal_statistics, deadline_us=D, budget_ncu=B)
    if ok(DCRV4QualityScheduler().schedule(inp)) or ok(DCRV3RescueScheduler().schedule(inp)):
        assert ok(got)
    md = Model.create(inp)
    if sum(md.cmin) <= md.B:
        assert got.internal_statistics["internal_compute_cost_ncu"] <= md.B
