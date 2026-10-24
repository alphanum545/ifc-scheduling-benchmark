"""The ablation harness must be faithful: its control reproduces DCR-v1 Admission exactly,
and every variant stays a valid, budget-safe DCR policy."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "historical"))

from algorithms.dcr_ablations import (  # noqa: E402
    BudgetRankScheduler, ControlScheduler, NoReserveScheduler, TimeRankScheduler,
    WeightedRankScheduler, ZeroPricesScheduler,
)
from algorithms.dcr_ifc.model import Model  # noqa: E402
from algorithms.dcr_ifc_v1 import DCRV1AdmissionScheduler  # noqa: E402
from test_dcr_v1 import random_input  # noqa: E402

VARIANTS = [NoReserveScheduler, ZeroPricesScheduler, TimeRankScheduler,
            BudgetRankScheduler, WeightedRankScheduler]
CASES = range(150)


@pytest.mark.parametrize("case", CASES)
def test_control_reproduces_dcr_v1_admission_decisions(case):
    inp = random_input(case)
    ref = DCRV1AdmissionScheduler().schedule(inp)
    got = ControlScheduler().schedule(inp)
    assert got.task_order == ref.task_order
    assert dict(got.resource_assignments) == dict(ref.resource_assignments)
    for key in ("planned_assignments_sha256", "internal_makespan_us", "internal_compute_cost_ncu",
                "first_fallback_step", "first_fallback_reason", "fallback_task_count"):
        assert got.internal_statistics.get(key) == ref.internal_statistics.get(key), key


@pytest.mark.parametrize("case", CASES)
def test_every_variant_is_complete_and_budget_safe(case):
    inp = random_input(case)
    md = Model.create(inp)
    for cls in VARIANTS:
        d = cls().schedule(inp)
        assert sorted(d.task_order) == sorted(md.tasks)
        assert set(d.resource_assignments) == set(md.tasks)
        if sum(md.cmin) <= md.B:  # raw cheapest-remaining invariant => never over budget
            assert d.internal_statistics["internal_compute_cost_ncu"] <= md.B, cls.__name__


def test_variants_differ_from_control_somewhere():
    """Each ablation must actually change behaviour on at least one synthetic case."""
    for cls in VARIANTS:
        assert any(cls().schedule(random_input(c)).resource_assignments
                   != ControlScheduler().schedule(random_input(c)).resource_assignments
                   for c in CASES), cls.__name__


def test_identities_are_distinct():
    ids = {cls.algorithm_id for cls in [ControlScheduler, *VARIANTS]}
    assert len(ids) == 6 and all(i.startswith("dcr_abl_") for i in ids)
