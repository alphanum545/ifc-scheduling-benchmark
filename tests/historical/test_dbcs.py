from __future__ import annotations

from fractions import Fraction

import pytest

from generator.reference_schedulers import _graph, _upward_ranks

from algorithms.common.interface import AlgorithmContractError, AlgorithmInput
from algorithms.dbcs import DBCSScheduler
from algorithms.dbcs.scheduler import _compute_subdeadlines, _quality_components
from algorithms.registry import stage4_registry
from experiment.runner import run_algorithm


def _single_task_instance(
    *,
    cheap_time_us: int = 10,
    cheap_cost_ncu: int = 1,
    fast_time_us: int = 1,
    fast_cost_ncu: int = 5,
    cheap_energy_nj: int = 100,
    fast_energy_nj: int = 1,
    resource_order: tuple[str, str] = ("r-cheap", "r-fast"),
) -> dict:
    resource_data = {
        "r-cheap": {"resource_id": "r-cheap", "tier": "iot"},
        "r-fast": {"resource_id": "r-fast", "tier": "cloud"},
    }
    return {
        "metadata": {"base_instance_id": "base-dbcs-single"},
        "tasks": [{"task_id": "T"}],
        "resources": [resource_data[resource_id] for resource_id in resource_order],
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
        instance_id="qos-dbcs",
        split="development",
        deadline_us=deadline_us,
        budget_ncu=budget_ncu,
    )


def _chain_instance() -> dict:
    return {
        "metadata": {"base_instance_id": "base-dbcs-chain"},
        "tasks": [{"task_id": "A"}, {"task_id": "B"}],
        "resources": [
            {"resource_id": "r1", "tier": "iot"},
            {"resource_id": "r2", "tier": "iot"},
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
            "A": {"r1": 4, "r2": 4},
            "B": {"r1": 3, "r2": 6},
        },
        "compute_cost_ncu": {
            "A": {"r1": 1, "r2": 2},
            "B": {"r1": 1, "r2": 2},
        },
        "compute_energy_nj": {
            "A": {"r1": 1, "r2": 1},
            "B": {"r1": 1, "r2": 1},
        },
    }


def test_subdeadline_equation_12_is_recursive_and_exact() -> None:
    instance = _chain_instance()
    graph = _graph(instance)
    _, _, average_communication = _upward_ranks(instance, graph)

    subdeadline = _compute_subdeadlines(
        instance,
        graph,
        average_communication,
        deadline_us=20,
    )

    assert subdeadline["B"] == 20
    assert subdeadline["A"] == 17


def test_quality_equations_13_through_16_are_exact() -> None:
    cheap = _quality_components(
        finish_us=10,
        subdeadline_us=Fraction(20, 1),
        finish_min_us=1,
        finish_max_us=10,
        cost_ncu=1,
        cost_min_ncu=1,
        cost_max_ncu=5,
        cost_best_ncu=5,
        cheapest_remaining_ncu=1,
        budget_unconsumed_ncu=5,
    )
    fast = _quality_components(
        finish_us=1,
        subdeadline_us=Fraction(20, 1),
        finish_min_us=1,
        finish_max_us=10,
        cost_ncu=5,
        cost_min_ncu=1,
        cost_max_ncu=5,
        cost_best_ncu=5,
        cheapest_remaining_ncu=1,
        budget_unconsumed_ncu=5,
    )

    assert cheap.time_q == Fraction(10, 9)
    assert cheap.cost_q == 1
    assert cheap.quality == Fraction(59, 45)
    assert fast.time_q == Fraction(19, 9)
    assert fast.cost_q == 0
    assert fast.quality == Fraction(19, 9)


def test_hard_cost_limit_filters_out_unaffordable_fast_resource() -> None:
    decision = DBCSScheduler().schedule(_input(budget_ncu=1, deadline_us=20))

    assert decision.resource_assignments == {"T": "r-cheap"}
    assert decision.internal_statistics["final_spare_budget_ncu"] == 0


def test_spare_budget_allows_faster_resource_when_quality_is_higher() -> None:
    decision = DBCSScheduler().schedule(_input(budget_ncu=5, deadline_us=20))

    assert decision.resource_assignments == {"T": "r-fast"}
    assert decision.internal_statistics["final_spare_budget_ncu"] == 0


def test_all_admissible_processors_missing_soft_subdeadline_selects_earliest_finish() -> None:
    decision = DBCSScheduler().schedule(_input(budget_ncu=5, deadline_us=1))

    assert decision.resource_assignments == {"T": "r-fast"}
    assert decision.internal_statistics["all_admissible_miss_subdeadline_count"] == 1
    assert decision.internal_statistics["paper_deadline_met"] is True


def test_paper_deadline_failure_is_retained_for_authoritative_measurement() -> None:
    result = run_algorithm(DBCSScheduler(), _input(budget_ncu=1, deadline_us=2))

    assert result.compute_cost_ncu == 1
    assert result.makespan_us == 10
    assert result.budget_met is True
    assert result.deadline_met is False
    assert result.joint_feasible is False
    assert result.algorithm_internal_statistics["paper_would_return_schedule"] is False


def test_budget_below_costcheapest_is_rejected_before_mapping() -> None:
    with pytest.raises(AlgorithmContractError, match="Costcheapest"):
        DBCSScheduler().schedule(_input(budget_ncu=0, deadline_us=20))


def test_equal_finish_and_cost_ranges_are_totalized_deterministically() -> None:
    instance = _single_task_instance(
        cheap_time_us=5,
        fast_time_us=5,
        cheap_cost_ncu=2,
        fast_cost_ncu=2,
        resource_order=("r-fast", "r-cheap"),
    )
    decision = DBCSScheduler().schedule(
        _input(budget_ncu=2, deadline_us=20, instance=instance)
    )

    assert decision.resource_assignments == {"T": "r-cheap"}
    assert decision.internal_statistics["zero_finish_spread_count"] == 1
    assert decision.internal_statistics["zero_cost_spread_count"] == 1


def test_energy_is_not_an_input_to_dbcs_resource_preference() -> None:
    high_cheap_energy = _single_task_instance(
        cheap_time_us=5,
        fast_time_us=5,
        cheap_cost_ncu=2,
        fast_cost_ncu=2,
        cheap_energy_nj=1_000_000,
        fast_energy_nj=1,
    )
    low_cheap_energy = _single_task_instance(
        cheap_time_us=5,
        fast_time_us=5,
        cheap_cost_ncu=2,
        fast_cost_ncu=2,
        cheap_energy_nj=1,
        fast_energy_nj=1_000_000,
    )

    first = DBCSScheduler().schedule(
        _input(budget_ncu=2, deadline_us=20, instance=high_cheap_energy)
    )
    second = DBCSScheduler().schedule(
        _input(budget_ncu=2, deadline_us=20, instance=low_cheap_energy)
    )

    assert first.resource_assignments == second.resource_assignments == {"T": "r-cheap"}


def test_dbcs_rejects_seed() -> None:
    with pytest.raises(AlgorithmContractError, match="deterministic"):
        DBCSScheduler().schedule(_input(budget_ncu=5, deadline_us=20), seed=7)


def test_dbcs_runs_through_authoritative_evaluator() -> None:
    result = run_algorithm(DBCSScheduler(), _input(budget_ncu=5, deadline_us=20))

    assert result.algorithm_id == "dbcs_ifc"
    assert result.algorithm_version == "dbcs_2016_ifc_adaptation_v1"
    assert result.schedule_id
    assert result.makespan_us == 1
    assert result.compute_cost_ncu == 5
    assert result.deadline_met is True
    assert result.budget_met is True
    assert result.joint_feasible is True
    assert result.algorithm_internal_statistics["faithfulness"] == "MINOR_IFC_ADAPTATION"


def test_stage4_registry_adds_dbcs() -> None:
    assert stage4_registry().ids() == (
        "bdheft_ifc_a05",
        "dbcs_ifc",
        "deterministic_heft_ifc",
        "deterministic_peft_ifc",
    )
