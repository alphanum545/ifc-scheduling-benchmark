"""DCR-v4 must be exactly the measured scoring-ablation variant and stay budget-safe."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "historical"))

from algorithms.dcr_ablations_scoring import BDCScoreScheduler  # noqa: E402
from algorithms.dcr_ifc.model import Model  # noqa: E402
from algorithms.dcr_ifc_v4 import DCRV4QualityScheduler  # noqa: E402
from test_dcr_v1 import random_input  # noqa: E402

CASES = range(150)


@pytest.mark.parametrize("case", CASES)
def test_v4_equals_measured_bdc_score_variant(case):
    inp = random_input(case)
    ref = BDCScoreScheduler().schedule(inp)
    got = DCRV4QualityScheduler().schedule(inp)
    assert got.task_order == ref.task_order
    assert dict(got.resource_assignments) == dict(ref.resource_assignments)
    assert got.internal_statistics.get("planned_assignments_sha256") == ref.internal_statistics.get("planned_assignments_sha256")


@pytest.mark.parametrize("case", CASES)
def test_v4_budget_safe(case):
    inp = random_input(case)
    md = Model.create(inp)
    if sum(md.cmin) <= md.B:
        assert DCRV4QualityScheduler().schedule(inp).internal_statistics["internal_compute_cost_ncu"] <= md.B


def test_v4_identity():
    assert DCRV4QualityScheduler.algorithm_id == "dcr_ifc_v4_quality"
