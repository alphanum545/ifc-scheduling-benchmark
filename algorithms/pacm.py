"""PACM (Cheng et al., 2025), fixed-pool adaptation of Algorithm 1."""
from collections import Counter
from functools import lru_cache
from math import sqrt
from random import Random

from generator.network import route_metrics
from generator.reference_schedulers import _candidate_assignment, _commit_assignment, _graph
from algorithms.common.interface import AlgorithmDecision


class PACMScheduler:
    algorithm_id = "pacm_ifc"
    algorithm_version = "fixed_pool_v1"

    def __init__(self, seed=0):
        self.seed = seed

    def schedule(self, scheduling_input, *, seed=None):
        inst = scheduling_input.instance
        g = _graph(inst)
        order = g.topological_order
        slots = g.resource_ids
        duration = inst["execution_time_us"]
        cost = inst["compute_cost_ncu"]
        deadline = scheduling_input.deadline_us
        rng = Random(self.seed if seed is None else seed)
        counts = Counter(g.resource_tiers.values())
        nslots = len(slots)
        # Integer units represent exact means over slots and distinct slot pairs.
        peers = max(1, nslots - 1)
        scale = nslots * peers
        fast = {t: min(duration[t].values()) * scale for t in order}
        mean = {t: sum(duration[t].values()) * peers for t in order}

        @lru_cache(maxsize=None)
        def mean_transfer(bits):
            total = 0
            for src, a in counts.items():
                for dst, b in counts.items():
                    pairs = a * (b - (src == dst))
                    if pairs:
                        delay = route_metrics(inst["network"], source_tier=src, target_tier=dst,
                                              same_resource=False, data_bits=bits)
                        total += pairs * delay["communication_time_us"]
            return total

        comm = {(p, t): mean_transfer(g.data_bits_by_edge[f"{p}->{t}"])
                for t in order for p in g.parents[t]}
        rank, up, latest = {}, {}, {}
        for t in reversed(order):
            tails = []
            for c in g.children[t]:
                delay = comm[t, c]
                # Eq. 13 uses the current task's fastest processing time.
                include = delay and rng.random() <= 1 - 1.5 ** (-fast[t] / delay)
                tails.append(rank[c] + (delay if include else 0))
            rank[t] = fast[t] + max(tails, default=0)
            up[t] = mean[t] + max((comm[t, c] + up[c] for c in g.children[t]), default=0)
            latest[t] = min((latest[c] - fast[c] - comm[t, c] for c in g.children[t]),
                            default=deadline * scale)

        down, distance = {}, {}
        for t in order:
            parents = g.parents[t]
            down[t] = max((down[p] + mean[p] + comm[p, t] for p in parents), default=0)
            # For tied longest prefixes, use the largest cumulative transfer delay.
            distance[t] = max((distance[p] + comm[p, t] for p in parents
                               if down[p] + mean[p] + comm[p, t] == down[t]), default=0)
        entry = max(rank.values())
        longest = max(up.values())
        indegree = {t: len(g.parents[t]) for t in order}
        edges = sum(indegree.values())
        n = len(order)
        variance_numerator = n * sum(k*k for k in indegree.values()) - edges*edges
        daf = n * max(indegree.values()) / sqrt(variance_numerator) if variance_numerator else 0
        placed, intervals = {}, {}
        priority = sorted(order, key=lambda t: -rank[t])
        for t in priority:
            critical = up[t] + down[t] == longest
            if critical:
                # Eq. 24, compare finish * entry * scale against an integer bound.
                bound = latest[t] * entry - distance[t] * (entry - rank[t])
            else:
                # Evaluate Eq. 22 in seconds, then convert the time-valued numerator
                # to scaled microseconds. For an edgeless graph the correction is zero.
                correction = daf * indegree[t] / edges if edges else 0
                bound = deadline * scale * (entry - rank[t] + fast[t] + correction * 1_000_000 * scale)

            def key(a):
                r, finish = a["resource_id"], a["end_us"]
                if critical or finish * scale * entry > bound:
                    return (1, finish, cost[t][r], r)
                return (0, cost[t][r], finish, r)

            candidates = (_candidate_assignment(inst, g, task_id=t, resource_id=r,
                          assignments=placed, intervals_by_resource=intervals) for r in slots)
            choice = min(candidates, key=key)
            _commit_assignment(placed, intervals, choice)
        return AlgorithmDecision(tuple(priority), {t: placed[t]["resource_id"] for t in order})
