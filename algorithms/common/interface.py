from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


class AlgorithmContractError(ValueError):
    """Raised when public experiment input or an algorithm decision is malformed."""


def _exact_int(value: Any, *, label: str, minimum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise AlgorithmContractError(f"{label} must be an exact integer >= {minimum}")
    return value


@dataclass(frozen=True)
class AlgorithmInput:
    """Only information that scheduling policy is allowed to consume.

    The complete QoS artifact is intentionally not stored here because it contains
    calibration metadata and a joint-feasibility witness that must remain hidden
    from publication algorithms.
    """

    instance: Mapping[str, Any]
    instance_id: str
    split: str
    deadline_us: int
    budget_ncu: int

    def __post_init__(self) -> None:
        if not isinstance(self.instance, Mapping):
            raise AlgorithmContractError("instance must be a base IFC mapping")
        if not isinstance(self.instance_id, str) or not self.instance_id:
            raise AlgorithmContractError("instance_id must be a non-empty string")
        if self.split not in {"development", "holdout"}:
            raise AlgorithmContractError("split must be 'development' or 'holdout'")
        _exact_int(self.deadline_us, label="deadline_us", minimum=1)
        _exact_int(self.budget_ncu, label="budget_ncu", minimum=0)

    @classmethod
    def from_artifacts(
        cls,
        *,
        base_instance: Mapping[str, Any],
        qos_instance: Mapping[str, Any],
        split: str,
    ) -> "AlgorithmInput":
        """Project a materialized QoS artifact onto the public scheduler view."""
        try:
            instance_id = qos_instance["instance_id"]
            qos_base_id = qos_instance["base_instance_id"]
            base_id = base_instance["metadata"]["base_instance_id"]
            deadline_us = qos_instance["deadline"]["deadline_us"]
            budget_ncu = qos_instance["budget"]["budget_ncu"]
        except (KeyError, TypeError) as exc:
            raise AlgorithmContractError(f"missing public scheduling field: {exc}") from exc
        if qos_base_id != base_id:
            raise AlgorithmContractError(
                "QoS artifact base_instance_id does not match the supplied base instance"
            )
        return cls(
            instance=base_instance,
            instance_id=instance_id,
            split=split,
            deadline_us=deadline_us,
            budget_ncu=budget_ncu,
        )


@dataclass(frozen=True)
class AlgorithmDecision:
    """Algorithm-owned policy output before authoritative schedule construction."""

    task_order: tuple[str, ...]
    resource_assignments: Mapping[str, str]
    internal_statistics: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task_order or any(
            not isinstance(task_id, str) or not task_id for task_id in self.task_order
        ):
            raise AlgorithmContractError("task_order must contain non-empty task IDs")
        if len(self.task_order) != len(set(self.task_order)):
            raise AlgorithmContractError("task_order must not contain duplicates")
        if not isinstance(self.resource_assignments, Mapping):
            raise AlgorithmContractError("resource_assignments must be a mapping")
        if set(self.resource_assignments) != set(self.task_order):
            raise AlgorithmContractError(
                "resource_assignments must cover exactly the tasks in task_order"
            )
        for task_id, resource_id in self.resource_assignments.items():
            if not isinstance(task_id, str) or not isinstance(resource_id, str) or not resource_id:
                raise AlgorithmContractError(
                    "resource_assignments must map task IDs to non-empty resource IDs"
                )
        if not isinstance(self.internal_statistics, Mapping):
            raise AlgorithmContractError("internal_statistics must be a mapping")


class Scheduler(Protocol):
    """Common publication-algorithm interface."""

    algorithm_id: str
    algorithm_version: str

    def schedule(
        self,
        scheduling_input: AlgorithmInput,
        *,
        seed: int | None = None,
    ) -> AlgorithmDecision:
        """Choose topological task order and task-to-resource mapping only."""
        ...
