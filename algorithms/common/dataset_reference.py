from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping

from generator.reference_schedulers import _candidate_assignment, _commit_assignment


def greedy_reference_mapping(
    instance: Mapping[str, Any],
    graph: Any,
    *,
    order: list[str],
    candidate_resources: Callable[[str], Iterable[str]],
    candidate_key: Callable[[str, str, dict[str, Any]], tuple[Any, ...]],
) -> dict[str, str]:
    """Extract the mapping phase used by Dataset's pinned greedy references.

    Candidate timing and interval insertion remain owned by Dataset private
    primitives. This helper only preserves the reference scheduler's selection
    loop so final authoritative evaluation can happen after the runtime timer.
    """
    assignments: dict[str, dict[str, Any]] = {}
    intervals: dict[str, tuple[dict[str, Any], ...]] = {}
    mapping: dict[str, str] = {}

    for task_id in order:
        candidates: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        for resource_id in candidate_resources(task_id):
            assignment = _candidate_assignment(
                instance,
                graph,
                task_id=task_id,
                resource_id=resource_id,
                assignments=assignments,
                intervals_by_resource=intervals,
            )
            candidates.append((candidate_key(task_id, resource_id, assignment), assignment))
        if not candidates:
            raise ValueError(f"task {task_id!r} has no candidate resource")
        _, selected = min(candidates, key=lambda item: item[0])
        mapping[task_id] = selected["resource_id"]
        _commit_assignment(assignments, intervals, selected)

    return mapping
