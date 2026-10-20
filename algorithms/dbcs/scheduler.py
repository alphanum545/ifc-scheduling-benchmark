from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from generator.reference_schedulers import (
    _candidate_assignment,
    _commit_assignment,
    _graph,
    _priority_order,
    _upward_ranks,
)

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput


@dataclass(frozen=True)
class _QualityComponents:
    time_q: Fraction
    cost_q: Fraction
    quality: Fraction
    meets_subdeadline: bool
    zero_finish_spread: bool
    zero_cost_spread: bool


def _compute_subdeadlines(
    instance: Mapping[str, Any],
    graph: Any,
    average_communication: Mapping[str, Fraction],
    *,
    deadline_us: int,
) -> dict[str, Fraction]:
    """Implement DBCS Eq. (12), with implicit zero-time dummy exit for multiple sinks."""
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
    return subdeadline


def _quality_components(
    *,
    finish_us: int,
    subdeadline_us: Fraction,
    finish_min_us: int,
    finish_max_us: int,
    cost_ncu: int,
    cost_min_ncu: int,
    cost_max_ncu: int,
    cost_best_ncu: int,
    cheapest_remaining_ncu: int,
    budget_unconsumed_ncu: int,
) -> _QualityComponents:
    """Implement DBCS Eqs. (13)-(16) using exact rational arithmetic."""
    if finish_max_us < finish_min_us:
        raise AlgorithmContractError("DBCS finish-time range is invalid")
    if cost_max_ncu < cost_min_ncu:
        raise AlgorithmContractError("DBCS cost range is invalid")
    if cheapest_remaining_ncu < 0 or budget_unconsumed_ncu < 0:
        raise AlgorithmContractError("DBCS remaining budget quantities must be non-negative")

    meets = Fraction(finish_us, 1) < subdeadline_us
    zero_finish_spread = finish_max_us == finish_min_us
    zero_cost_spread = cost_max_ncu == cost_min_ncu

    if zero_finish_spread:
        time_q = Fraction(0, 1)
    else:
        omega_deadline = subdeadline_us if meets else Fraction(0, 1)
        time_q = (omega_deadline - finish_us) / (finish_max_us - finish_min_us)

    if zero_cost_spread or not meets:
        cost_q = Fraction(0, 1)
    else:
        cost_q = Fraction(cost_best_ncu - cost_ncu, cost_max_ncu - cost_min_ncu)

    if budget_unconsumed_ncu == 0:
        if cheapest_remaining_ncu != 0:
            raise AlgorithmContractError(
                "DBCS has positive cheapest remaining cost with zero unconsumed budget"
            )
        cost_weight = Fraction(0, 1)
    else:
        cost_weight = Fraction(cheapest_remaining_ncu, budget_unconsumed_ncu)

    return _QualityComponents(
        time_q=time_q,
        cost_q=cost_q,
        quality=time_q + cost_q * cost_weight,
        meets_subdeadline=meets,
        zero_finish_spread=zero_finish_spread,
        zero_cost_spread=zero_cost_spread,
    )


class DBCSScheduler:
    """Paper-audited DBCS baseline adapted to the frozen IFC v1 resource/network model."""

    algorithm_id = "dbcs_ifc"
    algorithm_version = "dbcs_2016_ifc_adaptation_v1"

    def schedule(
        self,
        scheduling_input: AlgorithmInput,
        *,
        seed: int | None = None,
    ) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("DBCS is deterministic and does not accept a seed")

        instance = scheduling_input.instance
        graph = _graph(instance)
        upward, _, average_communication = _upward_ranks(instance, graph)
        order = _priority_order(graph, upward)
        subdeadlines = _compute_subdeadlines(
            instance,
            graph,
            average_communication,
            deadline_us=scheduling_input.deadline_us,
        )

        minimum_cost: dict[str, int] = {}
        maximum_cost: dict[str, int] = {}
        for task_id in graph.task_ids:
            task_costs = [
                int(instance["compute_cost_ncu"][task_id][resource_id])
                for resource_id in graph.resource_ids
            ]
            minimum_cost[task_id] = min(task_costs)
            maximum_cost[task_id] = max(task_costs)

        cheapest_total_ncu = sum(minimum_cost.values())
        if scheduling_input.budget_ncu < cheapest_total_ncu:
            raise AlgorithmContractError(
                "DBCS paper precondition failed: budget is below Costcheapest lower bound"
            )

        suffix_cheapest = [0] * (len(order) + 1)
        for position in range(len(order) - 1, -1, -1):
            suffix_cheapest[position] = suffix_cheapest[position + 1] + minimum_cost[order[position]]

        delta_cost_ncu = scheduling_input.budget_ncu - cheapest_total_ncu
        consumed_cost_ncu = 0
        assignments: dict[str, dict[str, Any]] = {}
        intervals: dict[str, tuple[dict[str, Any], ...]] = {}
        mapping: dict[str, str] = {}

        zero_finish_spread_count = 0
        zero_cost_spread_count = 0
        all_admissible_miss_deadline_count = 0

        for position, task_id in enumerate(order):
            budget_unconsumed_ncu = scheduling_input.budget_ncu - consumed_cost_ncu
            cheapest_remaining_ncu = suffix_cheapest[position]
            expected_delta = budget_unconsumed_ncu - cheapest_remaining_ncu
            if delta_cost_ncu != expected_delta or delta_cost_ncu < 0:
                raise AlgorithmContractError("DBCS spare-budget invariant was violated")

            candidates = {
                resource_id: _candidate_assignment(
                    instance,
                    graph,
                    task_id=task_id,
                    resource_id=resource_id,
                    assignments=assignments,
                    intervals_by_resource=intervals,
                )
                for resource_id in graph.resource_ids
            }
            finish_min_us = min(int(item["end_us"]) for item in candidates.values())
            finish_max_us = max(int(item["end_us"]) for item in candidates.values())

            earliest_resource = min(
                graph.resource_ids,
                key=lambda resource_id: (
                    int(candidates[resource_id]["end_us"]),
                    int(instance["compute_cost_ncu"][task_id][resource_id]),
                    resource_id,
                ),
            )
            cost_best_ncu = int(instance["compute_cost_ncu"][task_id][earliest_resource])

            cost_limit_ncu = minimum_cost[task_id] + delta_cost_ncu
            admissible = tuple(
                resource_id
                for resource_id in graph.resource_ids
                if int(instance["compute_cost_ncu"][task_id][resource_id]) <= cost_limit_ncu
            )
            if not admissible:
                raise AlgorithmContractError("DBCS produced an empty admissible processor set")

            quality_by_resource: dict[str, _QualityComponents] = {}
            for resource_id in admissible:
                quality_by_resource[resource_id] = _quality_components(
                    finish_us=int(candidates[resource_id]["end_us"]),
                    subdeadline_us=subdeadlines[task_id],
                    finish_min_us=finish_min_us,
                    finish_max_us=finish_max_us,
                    cost_ncu=int(instance["compute_cost_ncu"][task_id][resource_id]),
                    cost_min_ncu=minimum_cost[task_id],
                    cost_max_ncu=maximum_cost[task_id],
                    cost_best_ncu=cost_best_ncu,
                    cheapest_remaining_ncu=cheapest_remaining_ncu,
                    budget_unconsumed_ncu=budget_unconsumed_ncu,
                )

            sample_quality = next(iter(quality_by_resource.values()))
            if sample_quality.zero_finish_spread:
                zero_finish_spread_count += 1
            if sample_quality.zero_cost_spread:
                zero_cost_spread_count += 1
            if not any(item.meets_subdeadline for item in quality_by_resource.values()):
                all_admissible_miss_deadline_count += 1

            selected_resource = min(
                admissible,
                key=lambda resource_id: (
                    -quality_by_resource[resource_id].quality,
                    int(candidates[resource_id]["end_us"]),
                    int(instance["compute_cost_ncu"][task_id][resource_id]),
                    resource_id,
                ),
            )
            selected = candidates[selected_resource]
            selected_cost_ncu = int(instance["compute_cost_ncu"][task_id][selected_resource])

            mapping[task_id] = selected_resource
            _commit_assignment(assignments, intervals, selected)
            consumed_cost_ncu += selected_cost_ncu
            delta_cost_ncu -= selected_cost_ncu - minimum_cost[task_id]

        internal_makespan_us = max(int(assignment["end_us"]) for assignment in assignments.values())
        paper_deadline_met = internal_makespan_us <= scheduling_input.deadline_us

        return AlgorithmDecision(
            task_order=tuple(order),
            resource_assignments=mapping,
            internal_statistics={
                "paper": "Arabnejad-Barbosa-Prodan-2016",
                "doi": "10.1016/j.future.2015.07.021",
                "faithfulness": "MINOR_IFC_ADAPTATION",
                "cost_cheapest_lower_bound_ncu": cheapest_total_ncu,
                "final_spare_budget_ncu": delta_cost_ncu,
                "internal_makespan_us": internal_makespan_us,
                "paper_deadline_met": paper_deadline_met,
                "paper_would_return_schedule": paper_deadline_met,
                "zero_finish_spread_count": zero_finish_spread_count,
                "zero_cost_spread_count": zero_cost_spread_count,
                "all_admissible_miss_subdeadline_count": all_admissible_miss_deadline_count,
            },
        )
