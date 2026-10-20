"""Immutable public-input projection and exact DCR v0 preprocessing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from generator.network import resource_route_metrics
from generator.reference_schedulers import _graph
from algorithms.common.interface import AlgorithmContractError, AlgorithmInput

TIERS = ("iot", "fog", "cloud")


def exact(value: Any, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise AlgorithmContractError(f"{label} must be an exact integer >= {minimum}")
    return value


def overlap(start: int, finish: int, left: int, right: int) -> int:
    return max(0, min(finish, right) - max(start, left))


@dataclass(frozen=True)
class Model:
    instance: Mapping[str, Any]
    tasks: tuple[str, ...]
    resources: tuple[str, ...]
    tiers: tuple[str, ...]
    resource_tiers: dict[str, str]
    parents: tuple[tuple[int, ...], ...]
    children: tuple[tuple[int, ...], ...]
    topological: tuple[int, ...]
    bits: dict[tuple[int, int], int]
    p: tuple[tuple[int, ...], ...]
    c: tuple[tuple[int, ...], ...]
    pmin: tuple[int, ...]
    cmin: tuple[int, ...]
    a: tuple[int, ...]
    b: tuple[int, ...]
    h: tuple[int, ...]
    sigma: tuple[int, ...]
    theta: tuple[int, ...]
    g: tuple[tuple[tuple[int, ...], ...], ...]
    epochs: frozenset[int]
    D: int
    B: int
    H: int

    @classmethod
    def create(cls, inp: AlgorithmInput) -> "Model":
        instance = inp.instance
        graph = _graph(instance)
        tasks = tuple(sorted(graph.task_ids))
        resources = tuple(sorted(graph.resource_ids))
        if any(not isinstance(x, str) or not x for x in (*tasks, *resources)):
            raise AlgorithmContractError("task/resource IDs must be nonempty strings")
        tiers = tuple(graph.resource_tiers[r] for r in resources)
        if any(t not in TIERS for t in tiers):
            raise AlgorithmContractError("DCR v0 requires the frozen three-tier routing model")
        n, m = len(tasks), len(resources)
        index = {t: i for i, t in enumerate(tasks)}
        parents = tuple(tuple(index[t] for t in graph.parents[i]) for i in tasks)
        children = tuple(tuple(index[t] for t in graph.children[i]) for i in tasks)
        topological = tuple(index[t] for t in graph.topological_order)
        bits = {(index[p], index[ch]): graph.data_bits_by_edge[f"{p}->{ch}"]
                for p in tasks for ch in graph.children[p]}
        p = tuple(tuple(exact(instance['execution_time_us'][i][r], 'execution time', 1)
                        for r in resources) for i in tasks)
        c = tuple(tuple(exact(instance['compute_cost_ncu'][i][r], 'compute cost')
                        for r in resources) for i in tasks)
        D, B = exact(inp.deadline_us, 'deadline', 1), exact(inp.budget_ncu, 'budget')
        pmin, cmin = tuple(map(min, p)), tuple(map(min, c))
        a, h = [0] * n, [0] * n
        for i in topological:
            a[i] = max((a[j] + pmin[j] for j in parents[i]), default=0)
        for i in reversed(topological):
            h[i] = max((pmin[j] + h[j] for j in children[i]), default=0)
        b = tuple(D - h[i] for i in range(n))
        theta = tuple(sorted({D * k // 4 for k in (1, 2, 3, 4)} - {0}))
        g = tuple(tuple(tuple(max(0, p[i][r] - max(0, b[i] - t)) for t in theta)
                        for r in range(m)) for i in range(n))
        # Validate each realizable route category once, not all resource pairs/edges.
        exemplars = {t: [r for r in resources if graph.resource_tiers[r] == t][:2] for t in TIERS}
        if bits:
            for st in TIERS:
                for tt in TIERS:
                    if not exemplars[st] or not exemplars[tt]:
                        continue
                    src = exemplars[st][0]
                    dst = exemplars[tt][0] if st != tt else exemplars[tt][-1]
                    resource_route_metrics(instance['network'], graph.resource_tiers,
                        source_resource_id=src, target_resource_id=dst, data_bits=1)
        return cls(instance, tasks, resources, tiers, graph.resource_tiers,
                   parents, children, topological, bits, p, c, pmin, cmin,
                   tuple(a), b, tuple(h), tuple(b[i] - pmin[i] for i in range(n)),
                   theta, g, frozenset(n * k // 4 for k in (0, 1, 2, 3)), D, B, 2 * D * D)

    def delay(self, parent: int, child: int, src: int, dst: int) -> int:
        return resource_route_metrics(self.instance['network'], self.resource_tiers,
            source_resource_id=self.resources[src], target_resource_id=self.resources[dst],
            data_bits=self.bits[parent, child])['communication_time_us']
