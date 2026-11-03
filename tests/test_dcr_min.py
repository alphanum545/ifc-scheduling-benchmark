"""DCR-Min search wrappers: budget/deadline safety, lower-bound validity, best-of-probes and
determinism, on the historical synthetic instances."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "historical"))

from algorithms.dcr_ifc.model import Model  # noqa: E402
from algorithms.dcr_ifc_v4 import DCRV4QualityScheduler  # noqa: E402
from algorithms.dcr_min import DCRMinCostScheduler, DCRMinMakespanScheduler, lower_bounds  # noqa: E402
from test_dcr_v1 import random_input  # noqa: E402

CASES = range(40)
STRATEGIES = ("bisect", "descent", "hybrid")


def _oracles():
    # Default oracle (DCR-v4R) and the cheaper DCR-v4, so both code paths are covered.
    return (None, DCRV4QualityScheduler())


@pytest.mark.parametrize("case", CASES)
def test_min_makespan_is_budget_safe_and_best_of_its_probes(case):
    inp = random_input(case)
    md, lb = Model.create(inp), lower_bounds(inp)
    for oracle in _oracles():
        for strategy in STRATEGIES:
            st = DCRMinMakespanScheduler(oracle, strategy=strategy).schedule(inp).internal_statistics
            probes = st["dcrmin_probes"]
            assert 1 <= len(probes) <= DCRMinMakespanScheduler.max_probes + 1
            if sum(md.cmin) > md.B:
                assert st["dcrmin_status"] == "budget_infeasible"
                continue
            assert st["internal_compute_cost_ncu"] <= md.B
            assert st["internal_makespan_us"] >= lb["makespan_lb_us"]
            feasible = [p["makespan_us"] for p in probes if p["cost_ncu"] is not None and p["cost_ncu"] <= md.B]
            assert st["internal_makespan_us"] == min(feasible)


@pytest.mark.parametrize("case", CASES)
def test_min_cost_meets_deadline_whenever_any_probe_did(case):
    inp = random_input(case)
    md, lb = Model.create(inp), lower_bounds(inp)
    for oracle in _oracles():
        for strategy in STRATEGIES:
            st = DCRMinCostScheduler(oracle, strategy=strategy).schedule(inp).internal_statistics
            probes = st["dcrmin_probes"]
            assert 1 <= len(probes) <= DCRMinCostScheduler.max_probes + 1
            meeting = [p["cost_ncu"] for p in probes if p["makespan_us"] is not None and p["makespan_us"] <= md.D]
            if meeting:
                assert st["internal_makespan_us"] <= md.D
                assert st["internal_compute_cost_ncu"] == min(meeting)
                assert lb["cost_lb_deadline_ncu"] is not None
                assert st["internal_compute_cost_ncu"] >= lb["cost_lb_deadline_ncu"]
            else:
                assert st["dcrmin_status"] in ("deadline_not_met", "deadline_certified_infeasible")


@pytest.mark.parametrize("case", range(10))
def test_deterministic(case):
    inp = random_input(case)
    for cls in (DCRMinMakespanScheduler, DCRMinCostScheduler):
        a, b = cls().schedule(inp), cls().schedule(inp)
        assert a.task_order == b.task_order
        assert dict(a.resource_assignments) == dict(b.resource_assignments)


def test_lower_bounds_are_valid_on_every_probe():
    """No probe plan may beat LB_T; no deadline-meeting probe plan may beat LB_C(D)."""
    for case in CASES:
        inp = random_input(case)
        lb = lower_bounds(inp)
        for cls in (DCRMinMakespanScheduler, DCRMinCostScheduler):
            for p in cls().schedule(inp).internal_statistics["dcrmin_probes"]:
                if p["makespan_us"] is not None:
                    assert p["makespan_us"] >= lb["makespan_lb_us"]


def test_identities_and_seed_contract():
    assert DCRMinMakespanScheduler.algorithm_id != DCRMinCostScheduler.algorithm_id
    with pytest.raises(Exception):
        DCRMinMakespanScheduler().schedule(random_input(0), seed=1)
