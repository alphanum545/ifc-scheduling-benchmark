from __future__ import annotations

from fractions import Fraction

import pytest

from generator.reference_schedulers import _graph

from algorithms.bddc_bdc import BDCScheduler, BDDCScheduler
from algorithms.bddc_bdc.scheduler import (
    _bddc_budget_distribution,
    _deadline_distribution,
    _level_state,
    _quality,
)
from algorithms.common.interface import AlgorithmContractError, AlgorithmInput
from algorithms.registry import stage5_registry
from experiment.runner import run_algorithm


def _two_level_instance(
    *,
    cheap_energy_nj: int = 100,
    fast_energy_nj: int = 1,
) -> dict:
    return {
        "metadata": {"base_instance_id": "base-bddc-bdc-two-level"},
        "tasks": [{"task_id": "A"}, {"task_id": "B"}],
        "resources": [
            {"resource_id": "r-cheap", "tier": "iot"},
            {"resource_id": "r-fast", "tier": "iot"},
        ],
        "dependencies": [{"parent": "A", "child": "B", "data_bits": 0}],
        "network": {
            "segments": {
                "peer": {
                    "bandwidth_mbps": 100,
                    "latency_us": 0,
                    "energy_pj_per_bit": 0,
                }
            },
            "routes": {"iot_iot_different": ["peer"]},
        },
        "execution_time_us": {
            "A": {"r-cheap": 10, "r-fast": 1},
            "B": {"r-cheap": 9, "r-fast": 9},
        },
        "compute_cost_ncu": {
            "A": {"r-cheap": 1, "r-fast": 5},
            "B": {"r-cheap": 1, "r-fast": 1},
        },
        "compute_energy_nj": {
            "A": {"r-cheap": cheap_energy_nj, "r-fast": fast_energy_nj},
            "B": {"r-cheap": cheap_energy_nj, "r-fast": fast_energy_nj},
        },
    }


def _single_task_instance(
    *,
    first_resource: str = "r-fast",
    cheap_energy_nj: int = 100,
    fast_energy_nj: int = 1,
) -> dict:
    resources = {
        "r-cheap": {"resource_id": "r-cheap", "tier": "iot"},
        "r-fast": {"resource_id": "r-fast", "tier": "iot"},
    }
    second_resource = "r-cheap" if first_resource == "r-fast" else "r-fast"
    return {
        "metadata": {"base_instance_id": "base-bddc-bdc-single"},
        "tasks": [{"task_id": "T"}],
        "resources": [resources[first_resource], resources[second_resource]],
        "dependencies": [],
        "network": {"segments": {}, "routes": {}},
        "execution_time_us": {"T": {"r-cheap": 5, "r-fast": 5}},
        "compute_cost_ncu": {"T": {"r-cheap": 2, "r-fast": 2}},
        "compute_energy_nj": {
            "T": {"r-cheap": cheap_energy_nj, "r-fast": fast_energy_nj}
        },
    }


def _input(
    *,
    instance: dict,
    budget_ncu: int = 10,
    deadline_us: int = 100,
) -> AlgorithmInput:
    return AlgorithmInput(
        instance=instance,
        instance_id="qos-bddc-bdc",
        split="development",
        deadline_us=deadline_us,
        budget_ncu=budget_ncu,
    )


def test_bottom_depth_cp_time_and_static_est_follow_paper_structure() -> None:
    instance = _two_level_instance()
    graph = _graph(instance)
    state = _level_state(instance, graph)

    assert state.bottom_depth == {"B": 0, "A": 1}
    assert state.cp_time_us["A"] == 1
    assert state.cp_time_us["B"] == 9
    assert state.static_est_us["A"] == 0
    assert state.static_est_us["B"] == 1


def test_deadline_distribution_equation_11_is_cumulative() -> None:
    instance = _two_level_instance()
    graph = _graph(instance)
    state = _level_state(instance, graph)

    subdeadlines = _deadline_distribution(
        state,
        {"A", "B"},
        deadline_us=100,
    )

    assert subdeadlines[1] == 10
    assert subdeadlines[0] == 100


def test_bddc_budget_distribution_follows_algorithm1_non_cumulative_partition() -> None:
    instance = _two_level_instance()
    graph = _graph(instance)
    state = _level_state(instance, graph)

    subbudgets = _bddc_budget_distribution(
        state,
        {"A", "B"},
        remaining_budget_ncu=10,
    )

    assert subbudgets == {1: Fraction(1, 1), 0: Fraction(9, 1)}
    assert sum(subbudgets.values(), Fraction(0, 1)) == 10


def test_quality_equations_13_through_15_are_exact_at_preregistered_weight() -> None:
    tq, cq, quality = _quality(
        finish_us=10,
        finish_min_us=4,
        task_cost_ncu=6,
        task_cost_min_ncu=2,
        subdeadline_us=Fraction(20, 1),
        subbudget_ncu=Fraction(10, 1),
        omega_numerator=1,
        omega_denominator=2,
    )

    assert tq == Fraction(3, 10)
    assert cq == Fraction(1, 5)
    assert quality == Fraction(1, 4)


def test_bddc_and_bdc_preserve_distinct_budget_behaviour() -> None:
    scheduling_input = _input(instance=_two_level_instance())

    bddc = BDDCScheduler().schedule(scheduling_input)
    bdc = BDCScheduler().schedule(scheduling_input)

    assert bddc.resource_assignments["A"] == "r-cheap"
    assert bdc.resource_assignments["A"] == "r-fast"
    assert bddc.internal_statistics["budget_distribution"] == "algorithm1_level_partition"
    assert bdc.internal_statistics["budget_distribution"] == "whole_remaining_budget_per_task"
    assert bddc.internal_statistics["omega_numerator"] == 1
    assert bddc.internal_statistics["omega_denominator"] == 2
    assert bdc.internal_statistics["paper_default_omega_claimed"] is False


@pytest.mark.parametrize("scheduler", [BDDCScheduler(), BDCScheduler()])
def test_negative_quality_is_redistributed_only_once_per_single_task(scheduler) -> None:
    instance = {
        "metadata": {"base_instance_id": "base-negative-quality"},
        "tasks": [{"task_id": "T"}],
        "resources": [
            {"resource_id": "r-cheap", "tier": "iot"},
            {"resource_id": "r-fast", "tier": "iot"},
        ],
        "dependencies": [],
        "network": {"segments": {}, "routes": {}},
        "execution_time_us": {"T": {"r-cheap": 10, "r-fast": 5}},
        "compute_cost_ncu": {"T": {"r-cheap": 1, "r-fast": 2}},
        "compute_energy_nj": {"T": {"r-cheap": 1, "r-fast": 1}},
    }

    decision = scheduler.schedule(
        _input(instance=instance, budget_ncu=1, deadline_us=2)
    )

    assert decision.internal_statistics["redistribution_retry_count"] == 1
    assert decision.internal_statistics["negative_quality_after_retry_count"] == 1


@pytest.mark.parametrize("scheduler", [BDDCScheduler(), BDCScheduler()])
def test_adaptation_never_invents_elastic_resource_ids(scheduler) -> None:
    instance = _two_level_instance()
    decision = scheduler.schedule(_input(instance=instance))
    allowed = {resource["resource_id"] for resource in instance["resources"]}

    assert set(decision.resource_assignments.values()) <= allowed
    assert decision.internal_statistics["resource_model"] == "fixed_materialized_ifc_slots"
    assert decision.internal_statistics["paper_elastic_instance_provisioning_preserved"] is False
    assert decision.internal_statistics["paper_billing_cycle_cost_preserved"] is False
    assert decision.internal_statistics["faithfulness"] == "MAJOR_IFC_ADAPTATION"


@pytest.mark.parametrize("scheduler", [BDDCScheduler(), BDCScheduler()])
def test_energy_does_not_change_bddc_bdc_policy(scheduler) -> None:
    first = scheduler.schedule(
        _input(
            instance=_single_task_instance(
                cheap_energy_nj=1_000_000,
                fast_energy_nj=1,
            ),
            budget_ncu=10,
            deadline_us=20,
        )
    )
    second = scheduler.schedule(
        _input(
            instance=_single_task_instance(
                cheap_energy_nj=1,
                fast_energy_nj=1_000_000,
            ),
            budget_ncu=10,
            deadline_us=20,
        )
    )

    assert first.resource_assignments == second.resource_assignments == {"T": "r-cheap"}


@pytest.mark.parametrize("scheduler", [BDDCScheduler(), BDCScheduler()])
def test_bddc_bdc_reject_unused_seed(scheduler) -> None:
    with pytest.raises(AlgorithmContractError, match="deterministic"):
        scheduler.schedule(
            _input(instance=_two_level_instance()),
            seed=7,
        )


def test_bdc_runs_through_authoritative_evaluator_after_policy_timer() -> None:
    result = run_algorithm(
        BDCScheduler(),
        _input(instance=_two_level_instance()),
    )

    assert result.algorithm_id == "bdc_ifc_w05"
    assert result.algorithm_version == "bdc_2021_ifc_major_adaptation_v1"
    assert result.schedule_id
    assert result.makespan_us == 10
    assert result.compute_cost_ncu == 6
    assert result.deadline_met is True
    assert result.budget_met is True
    assert result.joint_feasible is True
    assert result.algorithm_internal_statistics["faithfulness"] == "MAJOR_IFC_ADAPTATION"


def test_bddc_runs_through_authoritative_evaluator_after_policy_timer() -> None:
    result = run_algorithm(
        BDDCScheduler(),
        _input(instance=_two_level_instance()),
    )

    assert result.algorithm_id == "bddc_ifc_w05"
    assert result.algorithm_version == "bddc_2021_ifc_major_adaptation_v1"
    assert result.schedule_id
    assert result.makespan_us == 19
    assert result.compute_cost_ncu == 2
    assert result.deadline_met is True
    assert result.budget_met is True
    assert result.joint_feasible is True
    assert result.algorithm_internal_statistics["faithfulness"] == "MAJOR_IFC_ADAPTATION"


def test_stage5_registry_adds_both_major_adaptations() -> None:
    assert stage5_registry().ids() == (
        "bdc_ifc_w05",
        "bddc_ifc_w05",
        "bdheft_ifc_a05",
        "dbcs_ifc",
        "deterministic_heft_ifc",
        "deterministic_peft_ifc",
    )
