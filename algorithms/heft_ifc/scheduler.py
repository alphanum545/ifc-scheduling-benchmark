from __future__ import annotations

from generator.reference_schedulers import (
    HEFT_IFC_ID,
    REFERENCE_SCHEDULER_VERSION,
    _graph,
    _priority_order,
    _upward_ranks,
)

from algorithms.common.dataset_reference import greedy_reference_mapping
from algorithms.common.interface import AlgorithmContractError, AlgorithmDecision, AlgorithmInput


class HeftIFCScheduler:
    """Decision-only adapter for Dataset's deterministic HEFT-IFC reference."""

    algorithm_id = HEFT_IFC_ID
    algorithm_version = REFERENCE_SCHEDULER_VERSION

    def schedule(
        self,
        scheduling_input: AlgorithmInput,
        *,
        seed: int | None = None,
    ) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("HEFT-IFC is deterministic and does not accept a seed")

        instance = scheduling_input.instance
        graph = _graph(instance)
        upward, _, _ = _upward_ranks(instance, graph)
        order = _priority_order(graph, upward)
        mapping = greedy_reference_mapping(
            instance,
            graph,
            order=order,
            candidate_resources=lambda _task: graph.resource_ids,
            candidate_key=lambda _task, resource, assignment: (
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
