from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

from algorithms.common.interface import AlgorithmInput
from algorithms.common.result import ScheduleResult


ExperimentStatus = Literal["success", "failed", "timeout"]
FailureStatus = Literal["failed", "timeout"]


def _non_empty(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _sha256(value: str, *, label: str) -> str:
    _non_empty(value, label=label)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value.lower()):
        raise ValueError(f"{label} must be a 64-character hexadecimal SHA-256")
    return value.lower()


def _exact_int(value: int, *, label: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{label} must be an exact integer >= {minimum}")
    return value


def _optional_exact_int(value: int | None, *, label: str, minimum: int = 0) -> None:
    if value is not None:
        _exact_int(value, label=label, minimum=minimum)


@dataclass(frozen=True)
class ExperimentResult:
    """Durable success/failure record for one independent scheduling job."""

    experiment_id: str
    job_id: str
    algorithm_id: str
    algorithm_version: str
    dataset_version: str
    dataset_artifact_sha256: str
    instance_id: str
    split: str
    seed: int | None
    repetition: int
    status: ExperimentStatus
    deadline_us: int
    budget_ncu: int
    schedule_id: str | None = None
    makespan_us: int | None = None
    compute_cost_ncu: int | None = None
    compute_energy_nj: int | None = None
    network_energy_pj: int | None = None
    deadline_met: bool | None = None
    budget_met: bool | None = None
    joint_feasible: bool | None = None
    algorithm_runtime_ns: int | None = None
    lambda_duration_ms: int | None = None
    algorithm_internal_statistics: Mapping[str, Any] = field(default_factory=dict)
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        for label in (
            "experiment_id",
            "job_id",
            "algorithm_id",
            "algorithm_version",
            "dataset_version",
            "instance_id",
        ):
            _non_empty(getattr(self, label), label=label)
        _sha256(self.dataset_artifact_sha256, label="dataset_artifact_sha256")
        if self.split not in {"development", "holdout"}:
            raise ValueError("split must be 'development' or 'holdout'")
        if self.seed is not None:
            _exact_int(self.seed, label="seed")
        _exact_int(self.repetition, label="repetition")
        if self.status not in {"success", "failed", "timeout"}:
            raise ValueError("status must be success, failed, or timeout")
        _exact_int(self.deadline_us, label="deadline_us", minimum=1)
        _exact_int(self.budget_ncu, label="budget_ncu")
        _optional_exact_int(self.lambda_duration_ms, label="lambda_duration_ms")
        if not isinstance(self.algorithm_internal_statistics, Mapping):
            raise ValueError("algorithm_internal_statistics must be a mapping")

        outcome_fields = (
            "makespan_us",
            "compute_cost_ncu",
            "compute_energy_nj",
            "network_energy_pj",
            "algorithm_runtime_ns",
        )
        feasibility_fields = ("deadline_met", "budget_met", "joint_feasible")

        if self.status == "success":
            _non_empty(self.schedule_id, label="schedule_id")
            for label in outcome_fields:
                value = getattr(self, label)
                if value is None:
                    raise ValueError(f"successful result requires {label}")
                _exact_int(value, label=label)
            for label in feasibility_fields:
                if not isinstance(getattr(self, label), bool):
                    raise ValueError(f"successful result requires boolean {label}")
            if self.error_type is not None or self.error_message is not None:
                raise ValueError("successful result must not contain error fields")
            return

        if self.status not in {"failed", "timeout"}:
            raise ValueError("unrecognized non-success status")
        _non_empty(self.error_type, label="error_type")
        _non_empty(self.error_message, label="error_message")
        if self.schedule_id is not None:
            raise ValueError("failed/timeout result must not contain schedule_id")
        for label in outcome_fields + feasibility_fields:
            if getattr(self, label) is not None:
                raise ValueError(f"failed/timeout result must not contain {label}")

    @classmethod
    def from_schedule_result(
        cls,
        result: ScheduleResult,
        *,
        experiment_id: str,
        job_id: str,
        dataset_version: str,
        dataset_artifact_sha256: str,
        repetition: int,
        lambda_duration_ms: int | None = None,
    ) -> "ExperimentResult":
        """Add orchestration/provenance fields after successful algorithm execution."""
        return cls(
            experiment_id=experiment_id,
            job_id=job_id,
            algorithm_id=result.algorithm_id,
            algorithm_version=result.algorithm_version,
            dataset_version=dataset_version,
            dataset_artifact_sha256=dataset_artifact_sha256,
            instance_id=result.instance_id,
            split=result.split,
            seed=result.seed,
            repetition=repetition,
            status="success",
            deadline_us=result.deadline_us,
            budget_ncu=result.budget_ncu,
            schedule_id=result.schedule_id,
            makespan_us=result.makespan_us,
            compute_cost_ncu=result.compute_cost_ncu,
            compute_energy_nj=result.compute_energy_nj,
            network_energy_pj=result.network_energy_pj,
            deadline_met=result.deadline_met,
            budget_met=result.budget_met,
            joint_feasible=result.joint_feasible,
            algorithm_runtime_ns=result.algorithm_runtime_ns,
            lambda_duration_ms=lambda_duration_ms,
            algorithm_internal_statistics=dict(result.algorithm_internal_statistics),
        )

    @classmethod
    def from_failure(
        cls,
        scheduling_input: AlgorithmInput,
        *,
        experiment_id: str,
        job_id: str,
        algorithm_id: str,
        algorithm_version: str,
        dataset_version: str,
        dataset_artifact_sha256: str,
        repetition: int,
        status: FailureStatus,
        error_type: str,
        error_message: str,
        seed: int | None = None,
        lambda_duration_ms: int | None = None,
    ) -> "ExperimentResult":
        """Create an explicit non-success record without fabricating schedule metrics."""
        if status not in {"failed", "timeout"}:
            raise ValueError("from_failure status must be failed or timeout")
        return cls(
            experiment_id=experiment_id,
            job_id=job_id,
            algorithm_id=algorithm_id,
            algorithm_version=algorithm_version,
            dataset_version=dataset_version,
            dataset_artifact_sha256=dataset_artifact_sha256,
            instance_id=scheduling_input.instance_id,
            split=scheduling_input.split,
            seed=seed,
            repetition=repetition,
            status=status,
            deadline_us=scheduling_input.deadline_us,
            budget_ncu=scheduling_input.budget_ncu,
            lambda_duration_ms=lambda_duration_ms,
            error_type=error_type,
            error_message=error_message,
        )
