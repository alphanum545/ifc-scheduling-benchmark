from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ScheduleResult:
    """One fully evaluated experiment result using exact benchmark units."""

    algorithm_id: str
    algorithm_version: str
    instance_id: str
    split: str
    seed: int | None
    schedule_id: str
    makespan_us: int
    compute_cost_ncu: int
    compute_energy_nj: int
    network_energy_pj: int
    deadline_us: int
    budget_ncu: int
    deadline_met: bool
    budget_met: bool
    joint_feasible: bool
    algorithm_runtime_ns: int
    algorithm_internal_statistics: Mapping[str, Any] = field(default_factory=dict)
