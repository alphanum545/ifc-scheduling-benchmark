"""Scoring ablation must be faithful: its control reproduces DCR-v1 Admission exactly, and the
BDC-score variant stays a valid, budget-safe DCR policy that differs somewhere."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "historical"))

from algorithms.dcr_ablations_scoring import BDCScoreScheduler, ScoringControlScheduler  # noqa: E402
from algorithms.dcr_ifc.model import Model  # noqa: E402
from algorithms.dcr_ifc_v1 import DCRV1AdmissionScheduler  # noqa: E402
from test_dcr_v1 import random_input  # noqa: E402

CASES = range(150)


@pytest.mark.parametrize("case", CASES)
def test_scoring_control_reproduces_dcr_v1_admission_decisions(case):
    inp = random_input(case)
    ref = DCRV1AdmissionScheduler().schedule(inp)
    got = ScoringControlScheduler().schedule(inp)
    assert got.task_order == ref.task_order
    assert dict(got.resource_assignments) == dict(ref.resource_assignments)
    for key in ("planned_assignments_sha256", "internal_makespan_us", "internal_compute_cost_ncu",
                "fallback_task_count", "first_fallback_step", "first_fallback_reason"):
        assert got.internal_statistics.get(key) == ref.internal_statistics.get(key), key


@pytest.mark.parametrize("case", CASES)
def test_bdc_score_is_complete_and_budget_safe(case):
    inp = random_input(case)
    md = Model.create(inp)
    got = BDCScoreScheduler().schedule(inp)
    assert set(got.resource_assignments) == set(md.tasks)
    if sum(md.cmin) <= md.B:
        assert got.internal_statistics["internal_compute_cost_ncu"] <= md.B


def test_bdc_score_differs_from_control_somewhere():
    assert any(BDCScoreScheduler().schedule(random_input(c)).resource_assignments
               != ScoringControlScheduler().schedule(random_input(c)).resource_assignments for c in CASES)


def test_identities_are_distinct():
    assert ScoringControlScheduler.algorithm_id != BDCScoreScheduler.algorithm_id
