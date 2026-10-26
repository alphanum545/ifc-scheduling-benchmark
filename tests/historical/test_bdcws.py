"""Hand-computed checks of BDCWS-IFC (docs/paper_audits/BDCWS_2023.md)."""
from __future__ import annotations

import pytest

from algorithms.bdcws import BDCWSScheduler
from algorithms.common.interface import AlgorithmContractError, AlgorithmInput


def _single(times: dict[str, int], costs: dict[str, int]) -> dict:
    return {
        "metadata": {"base_instance_id": "base-bdcws-single"},
        "tasks": [{"task_id": "T"}],
        "resources": [{"resource_id": r, "tier": "iot"} for r in times],
        "dependencies": [],
        "network": {"segments": {}, "routes": {}},
        "execution_time_us": {"T": dict(times)},
        "compute_cost_ncu": {"T": dict(costs)},
        "compute_energy_nj": {"T": {r: 1 for r in times}},
    }


def _chain() -> dict:
    return {
        "metadata": {"base_instance_id": "base-bdcws-chain"},
        "tasks": [{"task_id": "A"}, {"task_id": "B"}],
        "resources": [{"resource_id": "r1", "tier": "iot"}, {"resource_id": "r2", "tier": "iot"}],
        "dependencies": [{"parent": "A", "child": "B", "data_bits": 0}],
        "network": {
            "segments": {"peer": {"bandwidth_mbps": 100, "latency_us": 0, "energy_pj_per_bit": 0}},
            "routes": {"iot_iot_different": ["peer"]},
        },
        "execution_time_us": {"A": {"r1": 3, "r2": 4}, "B": {"r1": 3, "r2": 6}},
        "compute_cost_ncu": {"A": {"r1": 2, "r2": 1}, "B": {"r1": 1, "r2": 1}},
        "compute_energy_nj": {"A": {"r1": 1, "r2": 1}, "B": {"r1": 1, "r2": 1}},
    }


def _run(instance: dict, *, budget: int, deadline: int):
    inp = AlgorithmInput(instance=instance, instance_id="qos-bdcws", split="development",
                         deadline_us=deadline, budget_ncu=budget)
    return BDCWSScheduler().schedule(inp)


TWO = ({"cheap": 10, "fast": 1}, {"cheap": 1, "fast": 5})


# urank = ETmin = 1, ST_best = 0 (fast), OSD = D - 1, TOD = D, OSB = B - 1, TOAB = cost(slowest=cheap) + OSB = B.
@pytest.mark.parametrize(
    "budget, deadline, expected, branch",
    [
        # both affordable and timely: BF(cheap) = 10/(10*19) + 1/4 < BF(fast) = 1/(1*19) + 5/4
        (5, 20, "cheap", "bf"),
        # TOD = 5: only fast finishes before TOD
        (5, 5, "fast", "bf"),
        # TOAB = 4: only cheap affordable, and timely
        (4, 20, "cheap", "bf"),
        # only cheap affordable, not timely: earliest-finish affordable
        (4, 5, "cheap", "affordable_earliest"),
        # B = 0: TOAB = 0, nothing affordable, TOD = D > 0: cheapest
        (0, 5, "cheap", "empty_cheapest"),
    ],
)
def test_single_task_branches(budget, deadline, expected, branch):
    decision = _run(_single(*TWO), budget=budget, deadline=deadline)
    assert decision.resource_assignments["T"] == expected
    assert decision.internal_statistics["branch_counts"][branch] == 1


def test_empty_affordable_set_with_nonpositive_tod_takes_earliest_finish():
    # urank_B = 3, urank_A = 3 + 3 = 6; TOD_A = D - 6 + 3 = D - 3.
    # B = 0: OSB_A = -2, TOAB_A = cost(slowest r2) - 2 = -1 -> nothing affordable.
    tight = _run(_chain(), budget=0, deadline=2)  # TOD_A = -1 -> earliest finish r1 (3 < 4)
    relaxed = _run(_chain(), budget=0, deadline=10)  # TOD_A = 7 -> cheapest r2
    assert tight.resource_assignments["A"] == "r1"
    assert relaxed.resource_assignments["A"] == "r2"
    assert tight.internal_statistics["branch_counts"]["empty_tod_nonpositive"] >= 1


def test_nonpositive_spare_budget_uses_unit_denominator():
    # slowest = a (cost 3) > cheapest b (cost 1). B = 1: OSB = 0, TOAB = 3, affordable {a, b}, TOD = 20.
    # With denominator 1: BF(a) = 10/(10*19) + 3 > BF(b) = 5/(5*19) + 1 -> b. Literal Eq. (22) divides by zero.
    inst = _single({"a": 10, "b": 5, "c": 1}, {"a": 3, "b": 1, "c": 9})
    decision = _run(inst, budget=1, deadline=20)
    assert decision.resource_assignments["T"] == "b"
    assert decision.internal_statistics["osb_nonpositive_bf_count"] == 1


def test_deterministic_complete_and_topological():
    d1 = _run(_chain(), budget=3, deadline=12)
    d2 = _run(_chain(), budget=3, deadline=12)
    assert d1 == d2
    assert d1.task_order == ("A", "B") and set(d1.resource_assignments) == {"A", "B"}


def test_rejects_seed():
    inp = AlgorithmInput(instance=_chain(), instance_id="q", split="development", deadline_us=5, budget_ncu=5)
    with pytest.raises(AlgorithmContractError):
        BDCWSScheduler().schedule(inp, seed=1)
