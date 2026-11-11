"""Regression tests for the DCR-Cost study's source tracking and evidence joins."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from dcr_cost_study import pair_compact, plan_resume  # noqa: E402


def test_resume_requires_all_requested_algorithms_with_valid_current_source():
    plan = [{"instance_id": "a"}, {"instance_id": "b"}, {"instance_id": "c"}]
    hashes = {"dcr-cost-v2": "sha2", "dcr-cost-v3": "sha3"}

    def row(instance, algo, sha, *, valid="True", status="ok"):
        return {"instance_id": instance, "algo": algo, "source_sha256": sha,
                "status": status, "valid": valid}

    old = [
        row("a", "dcr-cost-v2", "sha2"), row("a", "dcr-cost-v3", "sha3"),
        row("b", "dcr-cost-v2", "sha2"),  # v3 is missing
        row("c", "dcr-cost-v2", "sha2"), row("c", "dcr-cost-v3", "stale"),
        row("c", "other", "sha_other"),
    ]
    retained, missing = plan_resume(old, plan, list(hashes), hashes)
    assert missing == {"b", "c"}
    assert {(r["instance_id"], r["algo"]) for r in retained} == {
        ("a", "dcr-cost-v2"), ("a", "dcr-cost-v3"), ("c", "other")}
    clean = [row("a", "dcr-cost-v2", "sha2"), row("a", "dcr-cost-v3", "sha3")]
    _, todo = plan_resume(clean, [plan[0]], list(hashes), hashes)
    assert todo == set()
    old.append(row("b", "dcr-cost-v3", "sha3", valid="False"))
    _, todo = plan_resume(old, plan, list(hashes), hashes)
    assert "b" in todo


def test_paired_evidence_requires_source_matched_baselines_and_valid_deadlines():
    entries = [{"instance_id": "id-b"}, {"instance_id": "id-a"}]
    compact = [
        {"index": "0", "v3_compute_cost_ncu": "80", "v3_makespan_us": "70",
         "v2_runtime_ms": "10", "v3_runtime_ms": "15"},
        {"index": "1", "v3_compute_cost_ncu": "120", "v3_makespan_us": "80",
         "v2_runtime_ms": "10", "v3_runtime_ms": "15"},
    ]
    old = [
        {"instance_id": "id-a", "source_sha256": "correct", "status": "ok", "valid": "True",
         "compute_cost_ncu": "100", "makespan_us": "75", "deadline_us": "100"},
        {"instance_id": "id-b", "source_sha256": "correct", "status": "ok", "valid": "True",
         "compute_cost_ncu": "120", "makespan_us": "85", "deadline_us": "100"},
    ]
    paired = pair_compact(compact, entries, old, "correct")
    assert [(r["instance_id"], r["v2_compute_cost_ncu"], r["v3_compute_cost_ncu"])
            for r in paired] == [("id-a", 100, 80), ("id-b", 120, 120)]
    with pytest.raises(ValueError, match="no validated"):
        pair_compact(compact, entries, old, "wrong")
    with pytest.raises(ValueError, match="duplicate"):
        pair_compact(compact + compact[:1], entries, old, "correct")
    late = [dict(compact[0], v3_makespan_us="101"), compact[1]]
    with pytest.raises(ValueError, match="deadline miss"):
        pair_compact(late, entries, old, "correct")
