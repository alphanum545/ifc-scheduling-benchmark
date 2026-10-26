from __future__ import annotations

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


def _min_time_upward_ranks(
    instance: Mapping[str, Any],
    graph: Any,
    average_communication: Mapping[str, Fraction],
) -> dict[str, Fraction]:
    """BDCWS Eq. (13): urank with the minimum execution time over all resources."""
    rank: dict[str, Fraction] = {}
    for task_id in reversed(graph.topological_order):
        minimum_execution = min(
            int(instance["execution_time_us"][task_id][resource_id]) for resource_id in graph.resource_ids
        )
        tail = max(
            (average_communication[f"{task_id}->{child}"] + rank[child] for child in graph.children[task_id]),
            default=Fraction(0, 1),
        )
        rank[task_id] = Fraction(minimum_execution, 1) + tail
    return rank


class BDCWSScheduler:
    """Paper-audited BDCWS (Zhou et al., Cluster Computing 2023) adapted to the frozen IFC v1 model.

    See docs/paper_audits/BDCWS_2023.md for every equation and adaptation decision.
    """

    algorithm_id = "bdcws_ifc"
    algorithm_version = "bdcws_2023_ifc_adaptation_v1"

    def schedule(
        self,
        scheduling_input: AlgorithmInput,
        *,
        seed: int | None = None,
    ) -> AlgorithmDecision:
        if seed is not None:
            raise AlgorithmContractError("BDCWS is deterministic and does not accept a seed")

        instance = scheduling_input.instance
        deadline = Fraction(scheduling_input.deadline_us, 1)
        budget_ncu = scheduling_input.budget_ncu
        graph = _graph(instance)
        resources = tuple(graph.resource_ids)
        _, _, average_communication = _upward_ranks(instance, graph)
        urank = _min_time_upward_ranks(instance, graph, average_communication)
        order = _priority_order(graph, urank)  # Table 2 line 3: ready task with the highest urank

        def cost(task_id: str, resource_id: str) -> int:
            return int(instance["compute_cost_ncu"][task_id][resource_id])

        def exec_time(task_id: str, resource_id: str) -> int:
            return int(instance["execution_time_us"][task_id][resource_id])

        minimum_cost = {t: min(cost(t, r) for r in resources) for t in graph.task_ids}
        # Eq. (17): cheapest cost of the unassigned tasks, current task included (T - T_assigned).
        suffix_cheapest = [0] * (len(order) + 1)
        for position in range(len(order) - 1, -1, -1):
            suffix_cheapest[position] = suffix_cheapest[position + 1] + minimum_cost[order[position]]

        assignments: dict[str, dict[str, Any]] = {}
        intervals: dict[str, tuple[dict[str, Any], ...]] = {}
        mapping: dict[str, str] = {}
        assigned_cost_ncu = 0
        branch_counts = {"empty_tod_nonpositive": 0, "empty_cheapest": 0, "bf": 0, "affordable_earliest": 0}
        osb_nonpositive_bf_count = 0

        for position, task_id in enumerate(order):
            if urank[task_id] <= 0:
                raise AlgorithmContractError("BDCWS urank must be positive (Eq. 21 divides by it)")
            candidates = {
                r: _candidate_assignment(
                    instance, graph, task_id=task_id, resource_id=r,
                    assignments=assignments, intervals_by_resource=intervals,
                )
                for r in resources
            }

            def finish(r: str) -> int:
                return int(candidates[r]["end_us"])

            # Definition 11: start time on the resource with the earliest finish time.
            best = min(resources, key=lambda r: (finish(r), cost(task_id, r), r))
            st_best = Fraction(int(candidates[best]["start_us"]), 1)
            et_min = min(exec_time(task_id, r) for r in resources)

            osd = deadline - st_best - urank[task_id]  # Eq. (15)
            tod = st_best + osd + et_min  # Eq. (14)

            osb = budget_ncu - assigned_cost_ncu - suffix_cheapest[position]  # Eq. (17)
            slowest = min(resources, key=lambda r: (-exec_time(task_id, r), cost(task_id, r), r))
            toab = cost(task_id, slowest) + osb  # Eq. (16), per-task cost on the slowest resource

            affordable = [r for r in resources if cost(task_id, r) <= toab]  # Eqs. (18)-(19), R u R' = all
            if not affordable:
                if tod <= 0:  # Table 2 lines 8-12
                    selected = min(resources, key=lambda r: (finish(r), cost(task_id, r), r))
                    branch_counts["empty_tod_nonpositive"] += 1
                else:  # lines 13-17
                    selected = min(resources, key=lambda r: (cost(task_id, r), finish(r), r))
                    branch_counts["empty_cheapest"] += 1
            else:
                timely = [r for r in affordable if finish(r) < tod]  # lines 20-21
                if timely:  # lines 22-25
                    if osd <= 0:
                        raise AlgorithmContractError("BDCWS branch (a) reached with OSD <= 0 (proved unreachable)")
                    cf_denominator = osb if osb > 0 else 1  # undefined case, see audit
                    if osb <= 0:
                        osb_nonpositive_bf_count += 1

                    def bf(r: str) -> Fraction:
                        tf = Fraction(finish(r), 1) / ((Fraction(exec_time(task_id, r), 1) / urank[task_id]) * osd)
                        cf = Fraction(cost(task_id, r), cf_denominator)
                        return tf + cf

                    selected = min(timely, key=lambda r: (bf(r), finish(r), cost(task_id, r), r))
                    branch_counts["bf"] += 1
                else:  # lines 26-30
                    selected = min(affordable, key=lambda r: (finish(r), cost(task_id, r), r))
                    branch_counts["affordable_earliest"] += 1

            mapping[task_id] = selected
            _commit_assignment(assignments, intervals, candidates[selected])
            assigned_cost_ncu += cost(task_id, selected)

        internal_makespan_us = max(int(a["end_us"]) for a in assignments.values())
        return AlgorithmDecision(
            task_order=tuple(order),
            resource_assignments=mapping,
            internal_statistics={
                "paper": "Zhou-Lin-Feng-Shi-Pang-2023",
                "doi": "10.1007/s10586-020-03176-1",
                "faithfulness": "MAJOR_IFC_ADAPTATION",
                "branch_counts": branch_counts,
                "osb_nonpositive_bf_count": osb_nonpositive_bf_count,
                "internal_cost_ncu": assigned_cost_ncu,
                "internal_makespan_us": internal_makespan_us,
            },
        )
