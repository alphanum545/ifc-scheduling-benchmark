from __future__ import annotations

from time import perf_counter_ns

from algorithms.common.interface import AlgorithmInput, Scheduler
from algorithms.common.result import ScheduleResult
from .evaluator_adapter import evaluate_decision


def run_algorithm(
    scheduler: Scheduler,
    scheduling_input: AlgorithmInput,
    *,
    seed: int | None = None,
) -> ScheduleResult:
    """Run algorithm policy, stop the timer, then evaluate authoritatively."""
    started_ns = perf_counter_ns()
    decision = scheduler.schedule(scheduling_input, seed=seed)
    runtime_ns = perf_counter_ns() - started_ns

    evaluation = evaluate_decision(scheduling_input, decision)
    if (
        evaluation.deadline_feasible is None
        or evaluation.budget_feasible is None
        or evaluation.joint_feasible is None
    ):
        raise RuntimeError("joint-constraint experiment produced incomplete feasibility")

    schedule = evaluation.schedule
    return ScheduleResult(
        algorithm_id=scheduler.algorithm_id,
        algorithm_version=scheduler.algorithm_version,
        instance_id=scheduling_input.instance_id,
        split=scheduling_input.split,
        seed=seed,
        schedule_id=schedule["schedule_id"],
        makespan_us=schedule["makespan_us"],
        compute_cost_ncu=schedule["compute_cost_ncu"],
        compute_energy_nj=schedule["compute_energy_nj"],
        network_energy_pj=schedule["network_energy_pj"],
        deadline_us=scheduling_input.deadline_us,
        budget_ncu=scheduling_input.budget_ncu,
        deadline_met=evaluation.deadline_feasible,
        budget_met=evaluation.budget_feasible,
        joint_feasible=evaluation.joint_feasible,
        algorithm_runtime_ns=runtime_ns,
        algorithm_internal_statistics=dict(decision.internal_statistics),
    )
