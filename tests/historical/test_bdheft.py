from __future__ import annotations

from fractions import Fraction

import pytest

from algorithms.bdheft import BDHEFTScheduler
from algorithms.bdheft.scheduler import _compute_thresholds, _mixed_score_numerator
from algorithms.common.interface import AlgorithmContractError, AlgorithmInput
from algorithms.registry import stage3_registry
from experiment.runner import run_algorithm


NCU = 1_000_000_000
SECOND_US = 1_000_000


def _single_task_instance(
    *,
    cheap_time_us: int = 10 * SECOND_US,
    cheap_cost_ncu: int = 1 * NCU,
    fast_time_us: int = 1 * SECOND_US,
    fast_cost_ncu: int = 5 * NCU,
    cheap_energy_nj: int = 10,
    fast_energy_nj: int = 1,
    cheap_price_ncu_per_second: int | None = None,
    fast_price_ncu_per_second: int | None = None,
) -> dict:
    cheap_resource = {"resource_id": "r-cheap", "tier": "iot"}
    fast_resource = {"resource_id": "r-fast", "tier": "cloud"}
    if cheap_price_ncu_per_second is not None:
        cheap_resource["price_ncu_per_second"] = cheap_price_ncu_per_second
    if fast_price_ncu_per_second is not None:
        fast_resource["price_ncu_per_second"] = fast_price_ncu_per_second
    return {
        "metadata": {"base_instance_id": "base-bdheft-single"},
        "tasks": [{"task_id": "T"}],
        "resources": [cheap_resource, fast_resource],
        "dependencies": [],
        "network": {"segments": {}, "routes": {}},
        "execution_time_us": {
            "T": {"r-cheap": cheap_time_us, "r-fast": fast_time_us},
        },
        "compute_cost_ncu": {
            "T": {"r-cheap": cheap_cost_ncu, "r-fast": fast_cost_ncu},
        },
        "compute_energy_nj": {
            "T": {"r-cheap": cheap_energy_nj, "r-fast": fast_energy_nj},
        },
    }


def _input(*, budget_ncu: int, deadline_us: int, instance: dict | None = None) -> AlgorithmInput:
    return AlgorithmInput(
        instance=_single_task_instance() if instance is None else instance,
        instance_id="qos-bdheft-single",
        split="development",
        deadline_us=deadline_us,
        budget_ncu=budget_ncu,
    )


def test_threshold_equations_8_through_13_are_exact() -> None:
    thresholds = _compute_thresholds(
        budget_ncu=100,
        deadline_us=200,
        allocated_cost_ncu=10,
        allocated_execution_us=30,
        average_cost_ncu=Fraction(20, 1),
        average_execution_us=Fraction(40, 1),
        remaining_average_cost_ncu=Fraction(50, 1),
        remaining_average_execution_us=Fraction(100, 1),
    )

    assert thresholds.swb_ncu == 40
    assert thresholds.swd_us == 70
    assert thresholds.baf == Fraction(2, 5)
    assert thresholds.daf == Fraction(2, 5)
    assert thresholds.ctb_ncu == 36
    assert thresholds.ctd_us == 68


def test_negative_spare_disables_adjustment_factor() -> None:
    thresholds = _compute_thresholds(
        budget_ncu=0,
        deadline_us=1,
        allocated_cost_ncu=0,
        allocated_execution_us=0,
        average_cost_ncu=Fraction(10, 1),
        average_execution_us=Fraction(20, 1),
        remaining_average_cost_ncu=Fraction(10, 1),
        remaining_average_execution_us=Fraction(20, 1),
    )

    assert thresholds.swb_ncu == -10
    assert thresholds.swd_us == -19
    assert thresholds.baf == 0
    assert thresholds.daf == 0
    assert thresholds.ctb_ncu == 10
    assert thresholds.ctd_us == 20


def test_equation_15_decodes_storage_units_without_normalization() -> None:
    one_second_zero_cost = _mixed_score_numerator(
        eft_us=SECOND_US,
        cost_ncu=0,
        alpha_numerator=1,
        alpha_denominator=2,
    )
    zero_time_one_cost_unit = _mixed_score_numerator(
        eft_us=0,
        cost_ncu=NCU,
        alpha_numerator=1,
        alpha_denominator=2,
    )

    assert one_second_zero_cost == zero_time_one_cost_unit == NCU


@pytest.mark.parametrize(
    ("budget_ncu", "deadline_us", "expected_resource", "expected_stat"),
    [
        (5 * NCU, 2 * SECOND_US, "r-fast", "paper_rule_1_count"),
        (3 * NCU, SECOND_US // 2, "r-fast", "paper_rule_2_count"),
        (0, SECOND_US // 2, "r-cheap", "paper_rule_3_count"),
        (0, 6 * SECOND_US, "r-cheap", "missing_paper_branch_count"),
    ],
)
def test_resource_selection_rules_and_missing_branch_totalization(
    budget_ncu: int,
    deadline_us: int,
    expected_resource: str,
    expected_stat: str,
) -> None:
    decision = BDHEFTScheduler().schedule(
        _input(budget_ncu=budget_ncu, deadline_us=deadline_us)
    )

    assert decision.resource_assignments == {"T": expected_resource}
    assert decision.internal_statistics[expected_stat] == 1
    assert sum(
        decision.internal_statistics[key]
        for key in (
            "paper_rule_1_count",
            "paper_rule_2_count",
            "paper_rule_3_count",
            "missing_paper_branch_count",
        )
    ) == 1


def test_cheapest_fallback_uses_current_task_execution_cost_not_price_rate() -> None:
    # With negative SWB/SWD, CTB and CTD equal the averages. The cheap resource
    # fails CTD while the fast resource fails CTB, forcing BS to be empty.
    # Advertised price rates intentionally point in the opposite direction.
    instance = _single_task_instance(
        cheap_time_us=2 * SECOND_US,
        cheap_cost_ncu=NCU,
        fast_time_us=SECOND_US,
        fast_cost_ncu=2 * NCU,
        cheap_price_ncu_per_second=10 * NCU,
        fast_price_ncu_per_second=1,
    )
    decision = BDHEFTScheduler().schedule(
        _input(budget_ncu=0, deadline_us=SECOND_US // 2, instance=instance)
    )

    assert decision.resource_assignments == {"T": "r-cheap"}
    assert decision.internal_statistics["paper_rule_3_count"] == 1


def test_energy_is_not_an_input_to_bdheft_resource_preference() -> None:
    instance = _single_task_instance(
        cheap_time_us=SECOND_US,
        cheap_cost_ncu=NCU,
        fast_time_us=SECOND_US,
        fast_cost_ncu=NCU,
        cheap_energy_nj=1_000_000,
        fast_energy_nj=1,
    )
    decision = BDHEFTScheduler().schedule(
        _input(budget_ncu=NCU, deadline_us=SECOND_US, instance=instance)
    )

    assert decision.resource_assignments == {"T": "r-cheap"}


def test_bdheft_rejects_seed() -> None:
    with pytest.raises(AlgorithmContractError, match="deterministic"):
        BDHEFTScheduler().schedule(
            _input(budget_ncu=5 * NCU, deadline_us=2 * SECOND_US),
            seed=7,
        )


def test_bdheft_runs_through_authoritative_evaluator() -> None:
    result = run_algorithm(
        BDHEFTScheduler(),
        _input(budget_ncu=5 * NCU, deadline_us=2 * SECOND_US),
    )

    assert result.algorithm_id == "bdheft_ifc_a05"
    assert result.algorithm_version == "bdheft_2015_ifc_adaptation_v1"
    assert result.schedule_id
    assert result.makespan_us == SECOND_US
    assert result.compute_cost_ncu == 5 * NCU
    assert result.deadline_met is True
    assert result.budget_met is True
    assert result.joint_feasible is True
    assert result.algorithm_internal_statistics["faithfulness"] == "MINOR_IFC_ADAPTATION"


def test_stage3_registry_adds_primary_bdheft_variant() -> None:
    assert stage3_registry().ids() == (
        "bdheft_ifc_a05",
        "deterministic_heft_ifc",
        "deterministic_peft_ifc",
    )
