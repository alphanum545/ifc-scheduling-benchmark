"""Policy-internal insertion calendar for a fixed task order and mapping.

The same rule DCR uses while it builds a plan (algorithms/dcr_ifc/state.py): a task becomes
ready at max over parents of (parent finish + route delay), and is inserted into the first idle
gap of its resource's calendar at or after that time. It is used only to *re-time* a plan after
a local reassignment; it is not the Dataset evaluator, and nothing here imports it. Agreement
with the evaluator is checked in tests/test_dcr_min_v2.py.
"""
from __future__ import annotations

from bisect import insort

from algorithms.dcr_ifc.model import Model


class Calendar:
    def __init__(self, md: Model, order: list[int]) -> None:
        self.md = md
        self.order = order
        self._delay: dict[tuple[int, int, int, int], int] = {}

    def delay(self, i: int, j: int, r: int, q: int) -> int:
        key = (i, j, r, q)
        d = self._delay.get(key)
        if d is None:
            d = 0 if r == q else self.md.delay(i, j, r, q)
            self._delay[key] = d
        return d

    def makespan(self, assign: list[int], cap: int | None = None) -> int:
        """Makespan of `order` under `assign`; returns as soon as any finish exceeds `cap`."""
        md, finish = self.md, [0] * len(assign)
        cals: list[list[tuple[int, int]]] = [[] for _ in md.resources]
        end = 0
        for i in self.order:
            r = assign[i]
            start = 0
            for j in md.parents[i]:
                t = finish[j] + self.delay(j, i, assign[j], r)
                if t > start:
                    start = t
            p = md.p[i][r]
            for left, right in cals[r]:
                if start + p <= left:
                    break
                if start < right:
                    start = right
            f = start + p
            if cap is not None and f > cap:
                return f
            insort(cals[r], (start, f))
            finish[i] = f
            if f > end:
                end = f
        return end
