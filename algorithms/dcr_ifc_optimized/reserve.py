"""Incremental exact totals for the unchanged three v0 price vectors."""
from algorithms.dcr_ifc.reserve import ReservePool as ReferencePool, dot


class ReservePool(ReferencePool):
    def __init__(self, state):
        super().__init__(state)
        self._order_size = None
        self._spent = 0
        self._capacity = []

    def refresh_minima(self, state):
        if self._order_size is None:
            super().refresh_minima(state)
        else:
            removed = state.order[self._order_size:]
            for ell, z in enumerate(self.prices):
                mins, weights = self.minimum[ell], self.weights[ell]
                total = self.totals[ell] + state.model.H * (state.spent - self._spent)
                for j in removed:
                    first, _ = mins.pop(j)
                    total -= weights[j][first]
                for j in state.dirty_domains:
                    if j not in mins:
                        continue
                    old_first, _ = mins[j]
                    first, second = self.choices[ell][j].top2(state.active[j])
                    if first is None:
                        raise ValueError('empty resource domain in current reserve')
                    total += weights[j][first] - weights[j][old_first]
                    mins[j] = (first, second)
                total += sum(dot(z[r], [old - new for old, new in
                                       zip(self._capacity[r], state.K[r])]) for r in range(len(z)))
                self.totals[ell] = total
            self.current = max(self.totals)
        self._order_size = len(state.order)
        self._spent = state.spent
        self._capacity = [row.copy() for row in state.K]
        state.dirty_domains.clear()
