from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from generator.reference_schedulers import (
    _communication_metrics,
    _graph,
    _priority_order,
    _upward_ranks,
)

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput


_US_PER_SECOND = 1_000_000
_NCU_PER_NORMALIZED_COST_UNIT = 1_000_000_000
_SCORE_TIME_MULTIPLIER = _NCU_PER_NORMALIZED_COST_UNIT // _US_PER_SECOND


@dataclass(frozen=True)
class _Thresholds:
    swb_ncu: Fraction
    swd_us: Fraction
    baf: Fraction
    daf: Fraction
    ctb_ncu: Fraction
    ctd_us: Fraction


def _mean_exact(values: list[int]) -> Fraction:
    if not values:
        raise AlgorithmContractError("BDHEFT requires at least one candidate resource")
    return Fraction(sum(values), len(values))


def _compute_thresholds(
    *,
    budget_ncu: int,
    deadline_us: int,
    allocated_cost_ncu: int,
    allocated_execution_us: int,
    average_cost_ncu: Fraction,
    average_execution_us: Fraction,
    remaining_average_cost_ncu: Fraction,
    remaining_average_execution_us: Fraction,
) -> _Thresholds:
    """Implement BDHEFT Eqs. (8)-(13) using exact rational arithmetic."""
    if remaining_average_cost_ncu <= 0:
        raise AlgorithmContractError("BDHEFT remaining average cost must be positive")
    if remaining_average_execution_us <= 0:
        raise AlgorithmContractError("BDHEFT remaining average execution time must be positive")

    swb = (
        Fraction(budget_ncu)
        - allocated_cost_ncu
        - remaining_average_cost_ncu
    )
    swd = (
        Fraction(deadline_us)
        - allocated_execution_us
        - remaining_average_execution_us
    )
    baf = (
        average_cost_ncu / remaining_average_cost_ncu
        if swb >= 0
        else Fraction(0, 1)
    )
    daf = (
        average_execution_us / remaining_average_execution_us
        if swd >= 0
        else Fraction(0, 1)
    )
    return _Thresholds(
        swb_ncu=swb,
        swd_us=swd,
        baf=baf,
        daf=daf,
        ctb_ncu=average_cost_ncu + swb * baf,
        ctd_us=average_execution_us + swd * daf,
    )


def _mixed_score_numerator(
    *,
    eft_us: int,
    cost_ncu: int,
    alpha_numerator: int,
    alpha_denominator: int,
) -> int:
    """Return an exact numerator for paper Eq. (15) in declared IFC base units.

    EFT is decoded from microseconds to seconds and cost from nano-normalized cost
    units to normalized cost units. The common positive denominator is omitted.
    """
    if (
        not isinstance(alpha_numerator, int)
        or isinstance(alpha_numerator, bool)
        or not isinstance(alpha_denominator, int)
        or isinstance(alpha_denominator, bool)
        or alpha_denominator <= 0
        or alpha_numerator < 0
        or alpha_numerator > alpha_denominator
    ):
        raise AlgorithmContractError("BDHEFT alpha must be an exact fraction in [0,1]")
    return (
        alpha_numerator * eft_us * _SCORE_TIME_MULTIPLIER
        + (alpha_denominator - alpha_numerator) * cost_ncu
    )


def _append_candidate(
    instance: Mapping[str, Any],
    graph: Any,
    *,
    task_id: str,
    resource_id: str,
    assignments: Mapping[str, Mapping[str, Any]],
    available_us: Mapping[str, int],
) -> dict[str, Any]:
    """Evaluate the paper's avail(resource) ready-time model without gap insertion."""
    duration_us = int(instance["execution_time_us"][task_id][resource_id])
    ready_us = 0
    for parent in graph.parents[task_id]:
        try:
            parent_assignment = assignments[parent]
        except KeyError as exc:
            raise AlgorithmContractError(
                f"BDHEFT considered task {task_id!r} before parent {parent!r}"
            ) from exc
        transfer_us = _communication_metrics(
            instance,
            graph,
            parent=parent,
            child=task_id,
            source_resource=parent_assignment["resource_id"],
            target_resource=resource_id,
        )["communication_time_us"]
        ready_us = max(ready_us, int(parent_assignment["end_us"]) + transfer_us)

    start_us = max(int(available_us.get(resource_id, 0)), ready_us)
    return {
        "task_id": task_id,
        "resource_id": resource_id,
        "start_us": start_us,
        "end_us": start_us + duration_us,
    }


class BDHEFTScheduler:
    """Audited BDHEFT-0.5 baseline adapted to the frozen IFC v1 model."""

    algorithm_id = "bdheft_ifc_a05"
    algorithm_version = "bdheft_2015_ifc_adaptation_v1"
    alpha_numerator = 1
    alpha_denominator = 2

    def schedule(
        self,
        scheduling_input: AlgorithmInput,
        *,
        seed: int | None = None,
    ) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("BDHEFT-0.5 is deterministic and does not accept a seed")

        instance = scheduling_input.instance
        graph = _graph(instance)
        upward, _, _ = _upward_ranks(instance, graph)
        order = _priority_order(graph, upward)

        average_cost: dict[str, Fraction] = {}
        average_execution: dict[str, Fraction] = {}
        for task_id in graph.task_ids:
            average_cost[task_id] = _mean_exact(
                [
                    int(instance["compute_cost_ncu"][task_id][resource_id])
                    for resource_id in graph.resource_ids
                ]
            )
            average_execution[task_id] = _mean_exact(
                [
                    int(instance["execution_time_us"][task_id][resource_id])
                    for resource_id in graph.resource_ids
                ]
            )

        suffix_cost: list[Fraction] = [Fraction(0, 1)] * (len(order) + 1)
        suffix_execution: list[Fraction] = [Fraction(0, 1)] * (len(order) + 1)
        for position in range(len(order) - 1, -1, -1):
            task_id = order[position]
            suffix_cost[position] = suffix_cost[position + 1] + average_cost[task_id]
            suffix_execution[position] = (
                suffix_execution[position + 1] + average_execution[task_id]
            )

        assignments: dict[str, dict[str, Any]] = {}
        available_us: dict[str, int] = {}
        mapping: dict[str, str] = {}
        allocated_cost_ncu = 0
        allocated_execution_us = 0
        selection_counts: Counter[str] = Counter()

        for position, task_id in enumerate(order):
            thresholds = _compute_thresholds(
                budget_ncu=scheduling_input.budget_ncu,
                deadline_us=scheduling_input.deadline_us,
                allocated_cost_ncu=allocated_cost_ncu,
                allocated_execution_us=allocated_execution_us,
                average_cost_ncu=average_cost[task_id],
                average_execution_us=average_execution[task_id],
                remaining_average_cost_ncu=suffix_cost[position],
                remaining_average_execution_us=suffix_execution[position],
            )

            candidates = {
                resource_id: _append_candidate(
                    instance,
                    graph,
                    task_id=task_id,
                    resource_id=resource_id,
                    assignments=assignments,
                    available_us=available_us,
                )
                for resource_id in graph.resource_ids
            }
            best_set = tuple(
                resource_id
                for resource_id in graph.resource_ids
                if int(instance["compute_cost_ncu"][task_id][resource_id])
                <= thresholds.ctb_ncu
                and int(instance["execution_time_us"][task_id][resource_id])
                <= thresholds.ctd_us
            )

            def score_key(resource_id: str) -> tuple[int, int, str]:
                candidate = candidates[resource_id]
                cost_ncu = int(instance["compute_cost_ncu"][task_id][resource_id])
                return (
                    _mixed_score_numerator(
                        eft_us=int(candidate["end_us"]),
                        cost_ncu=cost_ncu,
                        alpha_numerator=self.alpha_numerator,
                        alpha_denominator=self.alpha_denominator,
                    ),
                    int(candidate["end_us"]),
                    resource_id,
                )

            def cheapest_key(resource_id: str) -> tuple[int, int, str]:
                return (
                    int(instance["compute_cost_ncu"][task_id][resource_id]),
                    int(candidates[resource_id]["end_us"]),
                    resource_id,
                )

            if best_set:
                selected_resource = min(best_set, key=score_key)
                selection_rule = "paper_rule_1_best_set"
            elif thresholds.swb_ncu >= 0:
                selected_resource = min(graph.resource_ids, key=score_key)
                selection_rule = "paper_rule_2_score_all"
            elif thresholds.swd_us < 0:
                selected_resource = min(graph.resource_ids, key=cheapest_key)
                selection_rule = "paper_rule_3_cheapest"
            else:
                selected_resource = min(graph.resource_ids, key=cheapest_key)
                selection_rule = "ifc_totalization_missing_paper_branch"

            selected = candidates[selected_resource]
            assignments[task_id] = selected
            available_us[selected_resource] = int(selected["end_us"])
            mapping[task_id] = selected_resource
            allocated_cost_ncu += int(
                instance["compute_cost_ncu"][task_id][selected_resource]
            )
            allocated_execution_us += int(
                instance["execution_time_us"][task_id][selected_resource]
            )
            selection_counts[selection_rule] += 1

        return AlgorithmDecision(
            task_order=tuple(order),
            resource_assignments=mapping,
            internal_statistics={
                "paper": "Verma-Kaushal-2015",
                "doi": "10.1007/s10723-015-9344-9",
                "faithfulness": "MINOR_IFC_ADAPTATION",
                "alpha_numerator": self.alpha_numerator,
                "alpha_denominator": self.alpha_denominator,
                "score_time_unit": "second",
                "score_cost_unit": "normalized_cost_unit",
                "paper_rule_1_count": selection_counts["paper_rule_1_best_set"],
                "paper_rule_2_count": selection_counts["paper_rule_2_score_all"],
                "paper_rule_3_count": selection_counts["paper_rule_3_cheapest"],
                "missing_paper_branch_count": selection_counts[
                    "ifc_totalization_missing_paper_branch"
                ],
            },
        )
