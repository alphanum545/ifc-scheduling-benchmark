"""Monotone domains, exact insertion calendars, and exclusion caches."""
from __future__ import annotations

from bisect import insort
from .model import Model, TIERS, overlap


class MonotoneChoices:
    """Two DISTINCT resource alternatives from a fixed sorted list.

    Cursors only advance while domains shrink. No per-candidate resource scan.
    """
    def __init__(self, ordered: list[int]) -> None:
        self.ordered = ordered
        self.first = 0
        self.second = 1

    def top2(self, active: list[bool]) -> tuple[int | None, int | None]:
        order, end = self.ordered, len(self.ordered)
        while self.first < end and not active[order[self.first]]:
            self.first += 1
        if self.first == end:
            return None, None
        self.second = max(self.second, self.first + 1)
        while self.second < end and not active[order[self.second]]:
            self.second += 1
        return order[self.first], order[self.second] if self.second < end else None


class State:
    def __init__(self, model: Model) -> None:
        self.model = model
        n, m = len(model.tasks), len(model.resources)
        self.U = list(range(n))
        self.ready = {i for i in self.U if not model.parents[i]}
        self.indegree = [len(p) for p in model.parents]
        self.v = [[model.b[i] - model.a[i]] * m for i in self.U]
        self.rho = [[model.a[i]] * m for i in self.U]
        self.active = [[model.p[i][r] <= self.v[i][r] and
                        self.rho[i][r] + model.p[i][r] <= model.b[i]
                        for r in range(m)] for i in self.U]
        self.count = [sum(row) for row in self.active]
        self.K = [list(model.theta) for _ in range(m)]
        self.calendars: list[list[tuple[int, int, int]]] = [[] for _ in range(m)]
        self.placements: dict[int, tuple[int, int, int]] = {}
        self.order: list[int] = []
        self.spent = 0
        self.raw_reserve = sum(model.cmin)
        self.tier_choices = [{tier: MonotoneChoices(sorted(
            (r for r in range(m) if model.tiers[r] == tier),
            key=lambda r: (model.p[i][r] - model.b[i], r))) for tier in TIERS} for i in self.U]

    def choose_task(self) -> int:
        return min(self.ready, key=lambda i: (self.model.sigma[i], self.count[i], i))

    def insertion(self, i: int, r: int) -> tuple[int, int]:
        # For a ready task all parent arrivals are already exact. The static a_i
        # does not exceed the true readiness and hence cannot delay the task.
        start, p = self.rho[i][r], self.model.p[i][r]
        for left, right, _ in self.calendars[r]:
            if start + p <= left:
                break
            if start < right:
                start = right
        return start, start + p

    def capacity_deletions(self, i: int, r: int, start: int, finish: int) -> list[int] | None:
        md = self.model
        deleted = []
        for j in self.U:
            if j != i and self.active[j][r] and md.p[j][r] > (
                    self.v[j][r] - overlap(start, finish, md.a[j], md.b[j])):
                if self.count[j] == 1:
                    return None
                deleted.append(j)
        return deleted

    def children_fit(self, i: int, r: int, start: int, finish: int) -> bool:
        md = self.model
        for j in md.children[i]:
            fits = (self.active[j][r] and md.p[j][r] <= self.v[j][r] -
                    overlap(start, finish, md.a[j], md.b[j]) and finish + md.p[j][r] <= md.b[j])
            if fits:
                continue
            for tier in TIERS:
                first, second = self.tier_choices[j][tier].top2(self.active[j])
                q = second if first == r else first
                if q is not None and finish + md.delay(i, j, r, q) + md.p[j][q] <= md.b[j]:
                    fits = True
                    break
            if not fits:
                return False
        return True

    def _deactivate(self, i: int, r: int) -> None:
        if self.active[i][r]:
            self.active[i][r] = False
            self.count[i] -= 1

    def commit(self, i: int, r: int, start: int, finish: int) -> None:
        md = self.model
        insort(self.calendars[r], (start, finish, i))
        self.placements[i] = (r, start, finish)
        self.order.append(i)
        self.spent += md.c[i][r]
        self.raw_reserve -= md.cmin[i]
        self.U.remove(i)
        self.ready.remove(i)
        for j in self.U:
            self.v[j][r] -= overlap(start, finish, md.a[j], md.b[j])
            if md.p[j][r] > self.v[j][r]:
                self._deactivate(j, r)
        for k, theta in enumerate(md.theta):
            self.K[r][k] -= overlap(start, finish, 0, theta)
        for j in md.children[i]:
            for q in range(len(md.resources)):
                self.rho[j][q] = max(self.rho[j][q], finish + md.delay(i, j, r, q))
                if self.rho[j][q] + md.p[j][q] > md.b[j]:
                    self._deactivate(j, q)
            self.indegree[j] -= 1
            if self.indegree[j] == 0:
                self.ready.add(j)
