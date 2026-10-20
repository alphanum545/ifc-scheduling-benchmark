from __future__ import annotations

from generator.schedule import ScheduleEvaluation, build_schedule

from algorithms.common.interface import AlgorithmDecision, AlgorithmInput


def evaluate_decision(
    scheduling_input: AlgorithmInput,
    decision: AlgorithmDecision,
) -> ScheduleEvaluation:
    """Delegate final schedule construction and all metrics to Dataset."""
    return build_schedule(
        scheduling_input.instance,
        task_order=decision.task_order,
        resource_assignments=decision.resource_assignments,
        deadline_us=scheduling_input.deadline_us,
        budget_ncu=scheduling_input.budget_ncu,
    )
