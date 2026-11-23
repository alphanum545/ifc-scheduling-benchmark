"""DCDS fixed-pool adaptation of Lou et al., doi:10.1109/TMC.2022.3188770.

IFC virtual entry/exit have zero work and zero transfer. All non-cloud slots
are local candidates. Cloud selection uses real slot availability; the RTC
bound uses fastest cloud execution. The shared evaluator replays the final
topological order and mapping. A late schedule counts as a deadline miss.
"""
from collections import deque
from functools import lru_cache

from algorithms.common.interface import AlgorithmDecision
from generator.reference_schedulers import (
    _candidate_assignment, _commit_assignment, _communication_metrics, _graph,
)


class DCDSScheduler:
    algorithm_id = "dcds_ifc"
    algorithm_version = "fixed_pool_v1"

    def schedule(self, scheduling_input, *, seed=None):
        inst = scheduling_input.instance
        graph = _graph(inst)
        deadline = scheduling_input.deadline_us
        local = [r for r in graph.resource_ids if graph.resource_tiers[r].lower() != "cloud"]
        cloud = [r for r in graph.resource_ids if r not in local]
        if not local or not cloud:
            raise ValueError("DCDS requires local and cloud resources")
        duration = inst["execution_time_us"]
        cost = inst["compute_cost_ncu"]

        @lru_cache(maxsize=None)
        def transfer(t, child, r, dest):
            return _communication_metrics(inst, graph, parent=t, child=child,
                                         source_resource=r, target_resource=dest)["communication_time_us"]

        # Eq. 11 and 18, scaled to avoid rounding average route times.
        peers = max(1, len(local) - 1)
        scale = len(local) * peers
        delays = {}
        rank = {}
        rtc = {}
        for t in reversed(graph.topological_order):
            tails = []
            for child in graph.children[t]:
                delays[t, child] = {
                    r: sum(transfer(t, child, r, s) for s in local if s != r)
                    for r in local
                }
                tails.append(rank[child] + sum(delays[t, child].values()))
            rank[t] = peers * sum(duration[t][r] for r in local) + max(tails, default=0)
            rtc[t] = min(duration[t][r] for r in cloud) + max(
                (rtc[c] for c in graph.children[t]), default=0)
        entry = max(rank.values())
        latest = {t: deadline * (entry - rank[t]) for t in rank}
        order = sorted(graph.topological_order, key=lambda t: -rank[t])
        placed, intervals = {}, {}

        def candidate(t, r):
            return _candidate_assignment(inst, graph, task_id=t, resource_id=r,
                                         assignments=placed, intervals_by_resource=intervals)

        def edge_key(a):
            t, r, finish = a["task_id"], a["resource_id"], a["end_us"]
            late = max(((finish * peers + delays[t, c][r]) * entry - latest[c] * peers
                        for c in graph.children[t]), default=(finish - deadline) * peers * entry)
            return max(0, late), cost[t][r], finish, r

        for t in order:
            choice = min((candidate(t, r) for r in local), key=edge_key)
            _commit_assignment(placed, intervals, choice)
        late = [t for t in order if not graph.children[t] and placed[t]["end_us"] > deadline]
        offload = set(late)
        queue = deque(late)
        while queue:
            t = queue.popleft()
            required = list(graph.children[t])
            for p in graph.parents[t]:
                src = placed[p]["resource_id"]
                arrival = placed[p]["end_us"] + min(transfer(p, t, src, r) for r in cloud)
                if arrival + rtc[t] > deadline:
                    required.append(p)
            for task in required:
                if task not in offload:
                    offload.add(task)
                    queue.append(task)

        if offload:
            edge_plan = placed
            placed, intervals = {}, {}
            for t in order:
                if t in offload:
                    choice = min((candidate(t, r) for r in cloud),
                                 key=lambda a: (a["end_us"], cost[t][a["resource_id"]], a["resource_id"]))
                else:
                    choice = candidate(t, edge_plan[t]["resource_id"])
                _commit_assignment(placed, intervals, choice)

            # Algorithm 4. Reserve all other intervals while considering a move.
            for t in order:
                src = placed[t]["resource_id"]
                best = placed[t]
                for r in local:
                    if cost[t][r] >= cost[t][best["resource_id"]]:
                        continue
                    trial = candidate(t, r)
                    limit = min((placed[c]["start_us"] - transfer(t, c, r, placed[c]["resource_id"])
                                 for c in graph.children[t]), default=deadline)
                    if trial["end_us"] <= limit:
                        best = trial
                if best["resource_id"] != src:
                    intervals[src] = tuple(iv for iv in intervals[src] if iv["task_id"] != t)
                    _commit_assignment(placed, intervals, best)
        mapping = {t: placed[t]["resource_id"] for t in order}
        return AlgorithmDecision(tuple(order), mapping, {"offloading_set_size": len(offload)})
