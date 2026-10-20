from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from generator.reference_schedulers import (
    _candidate_assignment,
    _commit_assignment,
    _graph,
    _upward_ranks,
)

from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput


@dataclass(frozen=True)
class _LevelState:
    bottom_depth: Mapping[str, int]
    cp_time_us: Mapping[str, Fraction]
    static_est_us: Mapping[str, Fraction]


def _bottom_depths(graph: Any) -> dict[str, int]:
    """Implement paper Eq. (8) with an implicit zero-time dummy exit."""
    result: dict[str, int] = {}
    for task_id in reversed(graph.topological_order):
        children = graph.children[task_id]
        result[task_id] = 0 if not children else max(result[child] for child in children) + 1
    return result


def _level_state(instance: Mapping[str, Any], graph: Any) -> _LevelState:
    """Build paper Eqs. (3), (4), and (8) using route-aware average IFC communication."""
    _, _, average_communication = _upward_ranks(instance, graph)
    minimum_execution = {
        task_id: min(
            int(instance["execution_time_us"][task_id][resource_id])
            for resource_id in graph.resource_ids
        )
        for task_id in graph.task_ids
    }

    cp_time: dict[str, Fraction] = {}
    for task_id in graph.topological_order:
        parents = graph.parents[task_id]
        max_transfer = (
            max(average_communication[f"{parent}->{task_id}"] for parent in parents)
            if parents
            else Fraction(0, 1)
        )
        cp_time[task_id] = Fraction(minimum_execution[task_id], 1) + max_transfer

    static_est: dict[str, Fraction] = {}
    for task_id in graph.topological_order:
        parents = graph.parents[task_id]
        static_est[task_id] = (
            max(static_est[parent] + cp_time[parent] for parent in parents)
            if parents
            else Fraction(0, 1)
        )

    return _LevelState(
        bottom_depth=_bottom_depths(graph),
        cp_time_us=cp_time,
        static_est_us=static_est,
    )


def _active_level_weights(
    state: _LevelState,
    unscheduled: set[str],
) -> tuple[Fraction, dict[int, Fraction]]:
    if not unscheduled:
        raise AlgorithmContractError("BDDC/BDC distribution requires unscheduled tasks")
    level_weights: dict[int, Fraction] = {}
    for task_id in unscheduled:
        level_id = state.bottom_depth[task_id]
        level_weights[level_id] = level_weights.get(level_id, Fraction(0, 1)) + state.cp_time_us[task_id]
    sigma_weight = sum(level_weights.values(), Fraction(0, 1))
    if sigma_weight <= 0:
        raise AlgorithmContractError("BDDC/BDC sigmaWeight must be positive")
    return sigma_weight, level_weights


def _deadline_distribution(
    state: _LevelState,
    unscheduled: set[str],
    *,
    deadline_us: int,
) -> dict[int, Fraction]:
    """Implement cumulative paper Eq. (11) over the currently unscheduled levels."""
    sigma_weight, level_weights = _active_level_weights(state, unscheduled)
    cumulative = Fraction(0, 1)
    result: dict[int, Fraction] = {}
    for level_id in sorted(level_weights, reverse=True):
        cumulative += level_weights[level_id] * deadline_us / sigma_weight
        result[level_id] = cumulative
    return result


def _bddc_budget_distribution(
    state: _LevelState,
    unscheduled: set[str],
    *,
    remaining_budget_ncu: int,
) -> dict[int, Fraction]:
    """Implement Algorithm 1's non-cumulative BDDC budget partition."""
    sigma_weight, level_weights = _active_level_weights(state, unscheduled)
    return {
        level_id: level_weight * remaining_budget_ncu / sigma_weight
        for level_id, level_weight in level_weights.items()
    }


def _quality(
    *,
    finish_us: int,
    finish_min_us: int,
    task_cost_ncu: int,
    task_cost_min_ncu: int,
    subdeadline_us: Fraction,
    subbudget_ncu: Fraction,
    omega_numerator: int,
    omega_denominator: int,
) -> tuple[Fraction, Fraction, Fraction]:
    """Implement displayed paper Eqs. (13)-(15) exactly."""
    if subdeadline_us == 0:
        raise AlgorithmContractError("BDDC/BDC Eq. (13) is undefined for zero sub-deadline")
    if subbudget_ncu == 0:
        raise AlgorithmContractError("BDDC/BDC Eq. (14) is undefined for zero sub-budget")
    if (
        omega_denominator <= 0
        or omega_numerator < 0
        or omega_numerator > omega_denominator
    ):
        raise AlgorithmContractError("BDDC/BDC omega must be an exact fraction in [0,1]")

    tq = (subdeadline_us - finish_us - finish_min_us) / subdeadline_us
    cq = (subbudget_ncu - task_cost_ncu - task_cost_min_ncu) / subbudget_ncu
    quality = (
        omega_numerator * tq
        + (omega_denominator - omega_numerator) * cq
    ) / omega_denominator
    return tq, cq, quality


class _BaseBDDCScheduler:
    omega_numerator = 1
    omega_denominator = 2
    distribute_budget_by_level: bool
    algorithm_id: str
    algorithm_version: str
    paper_name: str

    def schedule(
        self,
        scheduling_input: AlgorithmInput,
        *,
        seed: int | None = None,
    ) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError(
                f"{self.paper_name} is deterministic and does not accept a seed"
            )

        instance = scheduling_input.instance
        graph = _graph(instance)
        state = _level_state(instance, graph)
        unscheduled = set(graph.task_ids)
        assignments: dict[str, dict[str, Any]] = {}
        intervals: dict[str, tuple[dict[str, Any], ...]] = {}
        mapping: dict[str, str] = {}
        order: list[str] = []
        consumed_budget_ncu = 0
        retry_count = 0
        negative_after_retry_count = 0

        subdeadlines = _deadline_distribution(
            state,
            unscheduled,
            deadline_us=scheduling_input.deadline_us,
        )
        level_subbudgets = (
            _bddc_budget_distribution(
                state,
                unscheduled,
                remaining_budget_ncu=scheduling_input.budget_ncu,
            )
            if self.distribute_budget_by_level
            else {}
        )

        while unscheduled:
            ready = tuple(
                task_id
                for task_id in unscheduled
                if all(parent in assignments for parent in graph.parents[task_id])
            )
            if not ready:
                raise AlgorithmContractError("BDDC/BDC could not find a ready task")
            task_id = min(ready, key=lambda item: (state.static_est_us[item], item))
            order.append(task_id)

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
            finish_min_us = min(int(candidate["end_us"]) for candidate in candidates.values())
            task_cost_min_ncu = min(
                int(instance["compute_cost_ncu"][task_id][resource_id])
                for resource_id in graph.resource_ids
            )

            def evaluate_current_distributions() -> dict[str, tuple[Fraction, Fraction, Fraction]]:
                level_id = state.bottom_depth[task_id]
                subdeadline = subdeadlines[level_id]
                remaining_budget = scheduling_input.budget_ncu - consumed_budget_ncu
                subbudget = (
                    level_subbudgets[level_id]
                    if self.distribute_budget_by_level
                    else Fraction(remaining_budget, 1)
                )
                return {
                    resource_id: _quality(
                        finish_us=int(candidates[resource_id]["end_us"]),
                        finish_min_us=finish_min_us,
                        task_cost_ncu=int(instance["compute_cost_ncu"][task_id][resource_id]),
                        task_cost_min_ncu=task_cost_min_ncu,
                        subdeadline_us=subdeadline,
                        subbudget_ncu=subbudget,
                        omega_numerator=self.omega_numerator,
                        omega_denominator=self.omega_denominator,
                    )
                    for resource_id in graph.resource_ids
                }

            quality_by_resource = evaluate_current_distributions()
            max_quality = max(values[2] for values in quality_by_resource.values())

            if max_quality < 0:
                retry_count += 1
                subdeadlines = _deadline_distribution(
                    state,
                    unscheduled,
                    deadline_us=scheduling_input.deadline_us,
                )
                if self.distribute_budget_by_level:
                    level_subbudgets = _bddc_budget_distribution(
                        state,
                        unscheduled,
                        remaining_budget_ncu=scheduling_input.budget_ncu - consumed_budget_ncu,
                    )
                quality_by_resource = evaluate_current_distributions()
                max_quality = max(values[2] for values in quality_by_resource.values())
                if max_quality < 0:
                    negative_after_retry_count += 1

            selected_resource = min(
                graph.resource_ids,
                key=lambda resource_id: (
                    -quality_by_resource[resource_id][2],
                    int(candidates[resource_id]["end_us"]),
                    int(instance["compute_cost_ncu"][task_id][resource_id]),
                    resource_id,
                ),
            )
            selected = candidates[selected_resource]
            selected_cost = int(instance["compute_cost_ncu"][task_id][selected_resource])

            mapping[task_id] = selected_resource
            _commit_assignment(assignments, intervals, selected)
            consumed_budget_ncu += selected_cost
            unscheduled.remove(task_id)

        internal_makespan_us = max(int(item["end_us"]) for item in assignments.values())
        return AlgorithmDecision(
            task_order=tuple(order),
            resource_assignments=mapping,
            internal_statistics={
                "paper": "Taghinezhad-Niar-Pashazadeh-Taheri-2021",
                "doi": "10.1007/s10586-021-03314-3",
                "paper_variant": self.paper_name,
                "faithfulness": "MAJOR_IFC_ADAPTATION",
                "omega_numerator": self.omega_numerator,
                "omega_denominator": self.omega_denominator,
                "paper_default_omega_claimed": False,
                "resource_model": "fixed_materialized_ifc_slots",
                "paper_elastic_instance_provisioning_preserved": False,
                "paper_billing_cycle_cost_preserved": False,
                "budget_distribution": (
                    "algorithm1_level_partition"
                    if self.distribute_budget_by_level
                    else "whole_remaining_budget_per_task"
                ),
                "redistribution_retry_count": retry_count,
                "negative_quality_after_retry_count": negative_after_retry_count,
                "internal_consumed_cost_ncu": consumed_budget_ncu,
                "internal_makespan_us": internal_makespan_us,
            },
        )


class BDDCScheduler(_BaseBDDCScheduler):
    """BDDC-IFC-0.5 major adaptation for the frozen fixed IFC resource pool."""

    algorithm_id = "bddc_ifc_w05"
    algorithm_version = "bddc_2021_ifc_major_adaptation_v1"
    paper_name = "BDDC"
    distribute_budget_by_level = True


class BDCScheduler(_BaseBDDCScheduler):
    """BDC-IFC-0.5 major adaptation for the frozen fixed IFC resource pool."""

    algorithm_id = "bdc_ifc_w05"
    algorithm_version = "bdc_2021_ifc_major_adaptation_v1"
    paper_name = "BDC"
    distribute_budget_by_level = False
