from __future__ import annotations

from generator.reference_schedulers import (
    PEFT_IFC_ID,
    REFERENCE_SCHEDULER_VERSION,
    _graph,
    _mean,
    _optimistic_cost_table,
    _priority_order,
)

from algorithms.common.dataset_reference import greedy_reference_mapping
from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput


class PeftIFCScheduler:
    """Decision-only adapter for Dataset's deterministic PEFT-IFC reference."""

    algorithm_id = PEFT_IFC_ID
    algorithm_version = REFERENCE_SCHEDULER_VERSION

    def schedule(
        self,
        scheduling_input: AlgorithmInput,
        *,
        seed: int | None = None,
    ) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("PEFT-IFC is deterministic and does not accept a seed")

        instance = scheduling_input.instance
        graph = _graph(instance)
        oct_table = _optimistic_cost_table(instance, graph)
        rank_oct = {
            task_id: _mean(oct_table[task_id][resource] for resource in graph.resource_ids)
            for task_id in graph.task_ids
        }
        order = _priority_order(graph, rank_oct)
        mapping = greedy_reference_mapping(
            instance,
            graph,
            order=order,
            candidate_resources=lambda _task: graph.resource_ids,
            candidate_key=lambda task, resource, assignment: (
                assignment["end_us"] + oct_table[task][resource],
                assignment["end_us"],
                resource,
            ),
        )
        return AlgorithmDecision(
            task_order=tuple(order),
            resource_assignments=mapping,
            internal_statistics={
                "reference_scheduler_id": self.algorithm_id,
                "reference_scheduler_version": self.algorithm_version,
            },
        )
