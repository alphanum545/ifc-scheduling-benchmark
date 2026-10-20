from __future__ import annotations

from fractions import Fraction

import pytest

from generator.reference_schedulers import _graph

from algorithms.bdsd import BDSDScheduler
from algorithms.bdsd.scheduler import _compute_subdeadlines
from algorithms.common.interface import AlgorithmContractError, AlgorithmInput
from algorithms.registry import stage8_registry
from experiment.runner import run_algorithm


def _single_task_instance(
    *,
    cheap_time_us: int = 10,
    cheap_cost_ncu: int = 1,
    fast_time_us: int = 1,
    fast_cost_ncu: int = 5,
    cheap_energy_nj: int = 100,
    fast_energy_nj: int = 1,
) -> dict:
    return {
        "metadata": {"base_instance_id": "base-bdsd-single"},
        "tasks": [{"task_id": "T"}],
        "resources": [
            {"resource_id": "r-cheap", "tier": "iot"},
            {"resource_id": "r-fast", "tier": "cloud"},
        ],
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
        instance_id="qos-bdsd",
        split="development",
        deadline_us=deadline_us,
        budget_ncu=budget_ncu,
    )


def _chain_instance() -> dict:
    return {
        "metadata": {"base_instance_id": "base-bdsd-chain"},
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


def _two_independent_tasks_instance() -> dict:
    return {
        "metadata": {"base_instance_id": "base-bdsd-fraction"},
        "tasks": [{"task_id": "A"}, {"task_id": "B"}],
        "resources": [
            {"resource_id": "r-cheap", "tier": "iot"},
            {"resource_id": "r-fast", "tier": "iot"},
        ],
        "dependencies": [],
        "network": {"segments": {}, "routes": {}},
        "execution_time_us": {
            "A": {"r-cheap": 10, "r-fast": 1},
            "B": {"r-cheap": 10, "r-fast": 1},
        },
        "compute_cost_ncu": {
            "A": {"r-cheap": 1, "r-fast": 2},
            "B": {"r-cheap": 1, "r-fast": 2},
        },
        "compute_energy_nj": {
            "A": {"r-cheap": 1, "r-fast": 1},
            "B": {"r-cheap": 1, "r-fast": 1},
        },
    }


def test_subdeadline_equation_12_is_recursive_and_exact() -> None:
    instance = _chain_instance()
    graph = _graph(instance)
    subdeadline, _ = _compute_subdeadlines(instance, graph, deadline_us=20)

    assert subdeadline["B"] == Fraction(20, 1)
    assert subdeadline["A"] == Fraction(17, 1)


def test_nonempty_affordable_set_chooses_earliest_finish() -> None:
    decision = BDSDScheduler().schedule(_input(budget_ncu=5, deadline_us=20))

    assert decision.resource_assignments == {"T": "r-fast"}
    assert decision.internal_statistics["empty_affordable_set_count"] == 0


def test_affordability_filter_excludes_fast_resource_when_erc_is_tight() -> None:
    decision = BDSDScheduler().schedule(_input(budget_ncu=1, deadline_us=20))

    assert decision.resource_assignments == {"T": "r-cheap"}
    assert decision.internal_statistics["empty_affordable_set_count"] == 0


def test_empty_affordable_set_uses_paper_cheapest_fallback() -> None:
    decision = BDSDScheduler().schedule(_input(budget_ncu=0, deadline_us=20))

    assert decision.resource_assignments == {"T": "r-cheap"}
    assert decision.internal_statistics["empty_affordable_set_count"] == 1
    assert decision.internal_statistics["paper_budget_met"] is False


def test_expected_reasonable_cost_uses_exact_fraction() -> None:
    decision = BDSDScheduler().schedule(
        _input(
            budget_ncu=3,
            deadline_us=50,
            instance=_two_independent_tasks_instance(),
        )
    )

    # First task sees erc = 3/2, so the cost-2 fast processor is not affordable.
    assert decision.task_order[0] == "A"
    assert decision.resource_assignments["A"] == "r-cheap"


def test_energy_is_not_an_input_to_bdsd_mapping() -> None:
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

    first = BDSDScheduler().schedule(
        _input(budget_ncu=2, deadline_us=20, instance=high_cheap_energy)
    )
    second = BDSDScheduler().schedule(
        _input(budget_ncu=2, deadline_us=20, instance=low_cheap_energy)
    )

    assert first.resource_assignments == second.resource_assignments


def test_bdsd_rejects_seed() -> None:
    with pytest.raises(AlgorithmContractError, match="deterministic"):
        BDSDScheduler().schedule(_input(budget_ncu=5, deadline_us=20), seed=7)


def test_bdsd_runs_through_authoritative_evaluator() -> None:
    result = run_algorithm(BDSDScheduler(), _input(budget_ncu=5, deadline_us=20))

    assert result.algorithm_id == "bdsd_ifc"
    assert result.algorithm_version == "bdsd_2019_ifc_adaptation_v1"
    assert result.schedule_id
    assert result.makespan_us == 1
    assert result.compute_cost_ncu == 5
    assert result.deadline_met is True
    assert result.budget_met is True
    assert result.joint_feasible is True
    assert result.algorithm_internal_statistics["faithfulness"] == "MINOR_IFC_ADAPTATION"


def test_stage8_registry_contains_seven_primary_comparators() -> None:
    assert stage8_registry().ids() == (
        "bdc_ifc_w05",
        "bddc_ifc_w05",
        "bdheft_ifc_a05",
        "bdsd_ifc",
        "dbcs_ifc",
        "deterministic_heft_ifc",
        "deterministic_peft_ifc",
    )
