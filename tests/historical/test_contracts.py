from __future__ import annotations

from algorithms.common.interface import AlgorithmDecision, AlgorithmInput
from experiment.result_schema import ExperimentResult
from experiment.runner import run_algorithm


def _base_instance() -> dict:
    return {
        "metadata": {"base_instance_id": "base-synthetic-1"},
        "tasks": [{"task_id": "A"}, {"task_id": "B"}],
        "resources": [
            {"resource_id": "iot-1", "tier": "iot"},
            {"resource_id": "fog-1", "tier": "fog"},
        ],
        "dependencies": [{"parent": "A", "child": "B", "data_bits": 0}],
        "network": {
            "tier_links": {
                "fog|iot": {
                    "bandwidth_bits_per_sec": 1_000_000,
                    "latency_us": 1,
                    "energy_pj_per_bit": 1,
                }
            }
        },
        "execution_time_us": {
            "A": {"iot-1": 10, "fog-1": 5},
            "B": {"iot-1": 10, "fog-1": 5},
        },
        "compute_cost_ncu": {
            "A": {"iot-1": 1, "fog-1": 3},
            "B": {"iot-1": 1, "fog-1": 3},
        },
        "compute_energy_nj": {
            "A": {"iot-1": 10, "fog-1": 8},
            "B": {"iot-1": 10, "fog-1": 8},
        },
    }


def _qos_instance() -> dict:
    return {
        "instance_id": "qos-synthetic-1",
        "base_instance_id": "base-synthetic-1",
        "deadline": {"deadline_us": 50},
        "budget": {"budget_ncu": 10},
        "calibration": {"secret": "must-not-enter-algorithm-input"},
        "joint_feasibility_witness": {"secret": "must-not-enter-algorithm-input"},
    }


def test_public_input_projects_only_allowed_qos_fields() -> None:
    scheduling_input = AlgorithmInput.from_artifacts(
        base_instance=_base_instance(),
        qos_instance=_qos_instance(),
        split="development",
    )

    assert scheduling_input.instance_id == "qos-synthetic-1"
    assert scheduling_input.deadline_us == 50
    assert scheduling_input.budget_ncu == 10
    assert not hasattr(scheduling_input, "calibration")
    assert not hasattr(scheduling_input, "joint_feasibility_witness")


class _SyntheticScheduler:
    algorithm_id = "synthetic"
    algorithm_version = "test-v1"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None):
        assert scheduling_input.split == "development"
        return AlgorithmDecision(
            task_order=("A", "B"),
            resource_assignments={"A": "fog-1", "B": "fog-1"},
            internal_statistics={"seed_seen": seed},
        )


def test_runner_uses_authoritative_evaluator_after_algorithm_decision() -> None:
    scheduling_input = AlgorithmInput.from_artifacts(
        base_instance=_base_instance(),
        qos_instance=_qos_instance(),
        split="development",
    )

    result = run_algorithm(_SyntheticScheduler(), scheduling_input, seed=7)

    assert result.algorithm_id == "synthetic"
    assert result.seed == 7
    assert result.makespan_us == 10
    assert result.compute_cost_ncu == 6
    assert result.compute_energy_nj == 16
    assert result.network_energy_pj == 0
    assert result.deadline_met is True
    assert result.budget_met is True
    assert result.joint_feasible is True
    assert result.algorithm_runtime_ns >= 0
    assert result.algorithm_internal_statistics == {"seed_seen": 7}


def test_experiment_result_adds_provenance_without_reentering_algorithm_policy() -> None:
    scheduling_input = AlgorithmInput.from_artifacts(
        base_instance=_base_instance(),
        qos_instance=_qos_instance(),
        split="development",
    )
    schedule_result = run_algorithm(_SyntheticScheduler(), scheduling_input, seed=7)

    result = ExperimentResult.from_schedule_result(
        schedule_result,
        experiment_id="exp-1",
        job_id="job-1",
        dataset_version="pilot-v1",
        dataset_artifact_sha256="a" * 64,
        repetition=0,
        lambda_duration_ms=12,
    )

    assert result.experiment_id == "exp-1"
    assert result.job_id == "job-1"
    assert result.dataset_version == "pilot-v1"
    assert result.dataset_artifact_sha256 == "a" * 64
    assert result.repetition == 0
    assert result.status == "success"
    assert result.lambda_duration_ms == 12
    assert result.algorithm_runtime_ns == schedule_result.algorithm_runtime_ns
