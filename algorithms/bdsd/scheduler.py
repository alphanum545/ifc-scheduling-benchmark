from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

from generator.reference_schedulers import _graph, _upward_ranks

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput


def _compute_subdeadlines(
    instance: Mapping[str, Any],
    graph: Any,
    *,
    deadline_us: int,
) -> tuple[dict[str, Fraction], Mapping[str, Fraction]]:
    """Implement BDSD Eq. (12) with the paper's average communication model."""
    _, _, average_communication = _upward_ranks(instance, graph)
    minimum_execution = {
        task_id: min(
            int(instance["execution_time_us"][task_id][resource_id])
            for resource_id in graph.resource_ids
        )
        for task_id in graph.task_ids
    }

    subdeadline: dict[str, Fraction] = {}
    for task_id in reversed(graph.topological_order):
        children = graph.children[task_id]
        if not children:
            subdeadline[task_id] = Fraction(deadline_us, 1)
            continue
        subdeadline[task_id] = min(
            subdeadline[child]
            - average_communication[f"{task_id}->{child}"]
            - minimum_execution[child]
            for child in children
        )
    return subdeadline, average_communication


def _paper_candidate(
    instance: Mapping[str, Any],
    graph: Any,
    average_communication: Mapping[str, Fraction],
    *,
    task_id: str,
    resource_id: str,
    assignments: Mapping[str, str],
    actual_finish: Mapping[str, Fraction],
    resource_available: Mapping[str, Fraction],
) -> tuple[Fraction, Fraction]:
    """Implement BDSD Eqs. (10)-(11) for one processor candidate."""
    parents = graph.parents[task_id]
    if parents:
        parent_ready = max(
            actual_finish[parent]
            + (
                Fraction(0, 1)
                if assignments[parent] == resource_id
                else average_communication[f"{parent}->{task_id}"]
            )
            for parent in parents
        )
    else:
        parent_ready = Fraction(0, 1)

    start = max(resource_available[resource_id], parent_ready)
    finish = start + int(instance["execution_time_us"][task_id][resource_id])
    return start, finish


class BDSDScheduler:
    """Full-paper-audited BDSD adapter for the frozen fixed IFC resource pool."""

    algorithm_id = "bdsd_ifc"
    algorithm_version = "bdsd_2019_ifc_adaptation_v1"

    def schedule(
        self,
        scheduling_input: AlgorithmInput,
        *,
        seed: int | None = None,
    ) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("BDSD is deterministic and does not accept a seed")

        instance = scheduling_input.instance
        graph = _graph(instance)
        subdeadline, average_communication = _compute_subdeadlines(
            instance,
            graph,
            deadline_us=scheduling_input.deadline_us,
        )

        topo_position = {
            task_id: index for index, task_id in enumerate(graph.topological_order)
        }
        order = tuple(
            sorted(
                graph.task_ids,
                key=lambda task_id: (
                    subdeadline[task_id],
                    topo_position[task_id],
                    task_id,
                ),
            )
        )

        assignments: dict[str, str] = {}
        actual_finish: dict[str, Fraction] = {}
        resource_available = {
            resource_id: Fraction(0, 1) for resource_id in graph.resource_ids
        }
        remaining_budget_ncu = scheduling_input.budget_ncu
        remaining_tasks = len(order)
        empty_affordable_count = 0
        selected_cost_ncu = 0

        for task_id in order:
            if any(parent not in assignments for parent in graph.parents[task_id]):
                raise AlgorithmContractError(
                    "BDSD SDL ordering violated task precedence after deterministic tie handling"
                )
            if remaining_tasks <= 0:
                raise AlgorithmContractError("BDSD remaining-task count became non-positive")

            expected_reasonable_cost = Fraction(remaining_budget_ncu, remaining_tasks)
            candidates: dict[str, tuple[Fraction, Fraction]] = {
                resource_id: _paper_candidate(
                    instance,
                    graph,
                    average_communication,
                    task_id=task_id,
                    resource_id=resource_id,
                    assignments=assignments,
                    actual_finish=actual_finish,
                    resource_available=resource_available,
                )
                for resource_id in graph.resource_ids
            }
            affordable = tuple(
                resource_id
                for resource_id in graph.resource_ids
                if int(instance["compute_cost_ncu"][task_id][resource_id])
                <= expected_reasonable_cost
            )

            if affordable:
                selected_resource = min(
                    affordable,
                    key=lambda resource_id: (
                        candidates[resource_id][1],
                        int(instance["compute_cost_ncu"][task_id][resource_id]),
                        resource_id,
                    ),
                )
            else:
                empty_affordable_count += 1
                selected_resource = min(
                    graph.resource_ids,
                    key=lambda resource_id: (
                        int(instance["compute_cost_ncu"][task_id][resource_id]),
                        candidates[resource_id][1],
                        resource_id,
                    ),
                )

            _, finish = candidates[selected_resource]
            task_cost = int(instance["compute_cost_ncu"][task_id][selected_resource])
            assignments[task_id] = selected_resource
            actual_finish[task_id] = finish
            resource_available[selected_resource] = finish
            remaining_budget_ncu -= task_cost
            selected_cost_ncu += task_cost
            remaining_tasks -= 1

        paper_makespan_us = max(actual_finish.values(), default=Fraction(0, 1))
        paper_deadline_met = paper_makespan_us <= scheduling_input.deadline_us
        paper_budget_met = selected_cost_ncu <= scheduling_input.budget_ncu

        return AlgorithmDecision(
            task_order=order,
            resource_assignments=assignments,
            internal_statistics={
                "paper": "Sun-Xiao-Xu-2019-BDSD",
                "doi": "10.1007/s10586-018-1751-9",
                "faithfulness": "MINOR_IFC_ADAPTATION",
                "task_priority": "ascending_recursive_subdeadline_eq12",
                "budget_rule": "remaining_budget_divided_by_unscheduled_task_count_eq14",
                "resource_rule": "earliest_finish_if_affordable_else_cheapest",
                "paper_selection_rule_typo_totalized_from_worked_example": True,
                "paper_timing_model": "append_availability_with_average_communication",
                "authoritative_cost_matrix_used": True,
                "empty_affordable_set_count": empty_affordable_count,
                "internal_selected_cost_ncu": selected_cost_ncu,
                "internal_remaining_budget_ncu": remaining_budget_ncu,
                "internal_makespan_us_numerator": paper_makespan_us.numerator,
                "internal_makespan_us_denominator": paper_makespan_us.denominator,
                "paper_deadline_met": paper_deadline_met,
                "paper_budget_met": paper_budget_met,
                "paper_schedule_success": paper_deadline_met and paper_budget_met,
            },
        )
