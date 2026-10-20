"""Three fixed-work scaled dual certificates; no LP or full-schedule lookahead."""
from __future__ import annotations

from .state import State, MonotoneChoices
from .model import overlap


def dot(a: tuple[int, ...] | list[int], b: tuple[int, ...] | list[int]) -> int:
    return sum(x * y for x, y in zip(a, b))


class ReservePool:
    def __init__(self, state: State) -> None:
        md = state.model
        m, k = len(md.resources), len(md.theta)
        zero = [[0] * k for _ in range(m)]
        self.prices = [zero]
        self.weights: list[dict[int, list[int]]] = []
        self.choices: list[dict[int, MonotoneChoices]] = []
        for ell in range(3):
            z = self.prices[ell]
            weights = {j: [md.H * md.c[j][r] + dot(z[r], md.g[j][r]) for r in range(m)]
                       for j in state.U}
            orders = {j: sorted((r for r in range(m) if state.active[j][r]),
                               key=lambda r: (weights[j][r], md.p[j][r], r)) for j in state.U}
            if any(not order for order in orders.values()):
                raise ValueError("cannot price an empty resource domain")
            self.weights.append(weights)
            self.choices.append({j: MonotoneChoices(order) for j, order in orders.items()})
            if ell < 2:
                demand = [[0] * k for _ in range(m)]
                for j, order in orders.items():
                    r = order[0]
                    for t in range(k):
                        demand[r][t] += md.g[j][r][t]
                scale = (2 if ell == 0 else 1) * max(md.B, 1)
                self.prices.append([[max(0, z[r][t] + scale * (demand[r][t] - state.K[r][t]))
                                     for t in range(k)] for r in range(m)])
        self.minimum: list[dict[int, tuple[int, int | None]]] = []
        self.totals: list[int] = []
        self.current = 0

    def refresh_minima(self, state: State) -> None:
        """Current bounds with the SAME prices; no stale prefix total is reused."""
        self.minimum = []
        self.totals = []
        for ell, z in enumerate(self.prices):
            minimum = {}
            total = state.model.H * state.spent
            for j in state.U:
                first, second = self.choices[ell][j].top2(state.active[j])
                if first is None:
                    raise ValueError("empty resource domain in current reserve")
                minimum[j] = (first, second)
                total += self.weights[ell][j][first]
            total -= sum(dot(z[r], state.K[r]) for r in range(len(z)))
            self.minimum.append(minimum)
            self.totals.append(total)
        self.current = max(self.totals)

    def after_candidate(self, state: State, i: int, r: int, start: int, finish: int,
                        deleted: list[int]) -> int:
        """O(number of affected tasks) via first/second distinct-resource minima."""
        md = state.model
        occupation = tuple(overlap(start, finish, 0, theta) for theta in md.theta)
        bounds = []
        for ell, z in enumerate(self.prices):
            w, mins = self.weights[ell], self.minimum[ell]
            value = (self.totals[ell] + md.H * md.c[i][r] - w[i][mins[i][0]] +
                     dot(z[r], occupation))
            for j in deleted:
                first, second = mins[j]
                if first == r:
                    if second is None:
                        raise ValueError("candidate deletes the only active resource")
                    value += w[j][second] - w[j][first]
            bounds.append(value)
        bound = max(bounds)
        if bound < self.current:
            raise ArithmeticError("same-pool candidate reserve unexpectedly decreased")
        return bound
