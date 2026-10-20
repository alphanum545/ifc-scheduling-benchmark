from __future__ import annotations

import pytest

from generator.reference_schedulers import schedule_heft_ifc, schedule_peft_ifc

from algorithms.common.interface import AlgorithmContractError, AlgorithmInput
from algorithms.heft_ifc import HeftIFCScheduler
from algorithms.peft_ifc import PeftIFCScheduler
from algorithms.registry import stage2_registry
from experiment.evaluator_adapter import evaluate_decision
from experiment.runner import run_algorithm


def _base_instance() -> dict:
    return {
        "metadata": {"base_instance_id": "base-reference-adapter-1"},
        "tasks": [{"task_id": "A"}, {"task_id": "B"}, {"task_id": "C"}],
        "resources": [
            {"resource_id": "fog-1", "tier": "fog"},
            {"resource_id": "iot-1", "tier": "iot"},
        ],
        "dependencies": [
            {"parent": "A", "child": "B", "data_bits": 1_000},
            {"parent": "A", "child": "C", "data_bits": 8_000},
        ],
        "network": {
            "segments": {
                "if": {
                    "bandwidth_mbps": 100,
                    "latency_us": 7,
                    "energy_pj_per_bit": 2,
                }
            },
            "routes": {"iot_fog": ["if"]},
        },
        "execution_time_us": {
            "A": {"fog-1": 7, "iot-1": 12},
            "B": {"fog-1": 15, "iot-1": 5},
            "C": {"fog-1": 4, "iot-1": 11},
        },
        "compute_cost_ncu": {
            "A": {"fog-1": 5, "iot-1": 1},
            "B": {"fog-1": 6, "iot-1": 1},
            "C": {"fog-1": 4, "iot-1": 1},
        },
        "compute_energy_nj": {
            "A": {"fog-1": 8, "iot-1": 10},
            "B": {"fog-1": 12, "iot-1": 7},
            "C": {"fog-1": 6, "iot-1": 9},
        },
    }


def _input(*, deadline_us: int = 1_000, budget_ncu: int = 1_000) -> AlgorithmInput:
    return AlgorithmInput(
        instance=_base_instance(),
        instance_id="qos-reference-adapter-1",
        split="development",
        deadline_us=deadline_us,
        budget_ncu=budget_ncu,
    )


@pytest.mark.parametrize(
    ("scheduler", "reference"),
    [
        (HeftIFCScheduler(), schedule_heft_ifc),
        (PeftIFCScheduler(), schedule_peft_ifc),
    ],
)
def test_adapter_rebuilds_exact_dataset_reference_schedule(scheduler, reference) -> None:
    scheduling_input = _input()
    decision = scheduler.schedule(scheduling_input)
    rebuilt = evaluate_decision(scheduling_input, decision)
    direct = reference(scheduling_input.instance)

    assert rebuilt.schedule == direct.schedule
    assert rebuilt.schedule["schedule_id"] == direct.schedule["schedule_id"]


@pytest.mark.parametrize("scheduler", [HeftIFCScheduler(), PeftIFCScheduler()])
def test_reference_policy_is_independent_of_deadline_and_budget(scheduler) -> None:
    loose = scheduler.schedule(_input(deadline_us=10_000, budget_ncu=10_000))
    tight = scheduler.schedule(_input(deadline_us=1, budget_ncu=0))

    assert tight == loose


@pytest.mark.parametrize("scheduler", [HeftIFCScheduler(), PeftIFCScheduler()])
def test_deterministic_reference_rejects_seed(scheduler) -> None:
    with pytest.raises(AlgorithmContractError, match="deterministic"):
        scheduler.schedule(_input(), seed=1)


def test_stage2_registry_exposes_reference_ids() -> None:
    assert stage2_registry().ids() == ("deterministic_heft_ifc", "deterministic_peft_ifc")


def test_runner_reports_reference_metrics_after_decision_only_runtime() -> None:
    scheduling_input = _input()
    result = run_algorithm(HeftIFCScheduler(), scheduling_input)
    direct = schedule_heft_ifc(scheduling_input.instance).schedule

    assert result.schedule_id == direct["schedule_id"]
    assert result.makespan_us == direct["makespan_us"]
    assert result.compute_cost_ncu == direct["compute_cost_ncu"]
    assert result.compute_energy_nj == direct["compute_energy_nj"]
    assert result.network_energy_pj == direct["network_energy_pj"]
    assert result.seed is None
    assert result.algorithm_runtime_ns >= 0
