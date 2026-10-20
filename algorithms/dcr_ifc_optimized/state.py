"""Exact v0 state with cheap capacity screening and domain-change tracking."""
from algorithms.dcr_ifc.state import State as ReferenceState


class State(ReferenceState):
    def __init__(self, model):
        super().__init__(model)
        self.dirty_domains: set[int] = set()

    def _deactivate(self, i: int, r: int) -> None:
        if self.active[i][r]:
            self.dirty_domains.add(i)
        super()._deactivate(i, r)

    def capacity_deletions(self, i, r, start, finish):
        md = self.model
        active, v, p, a, b, count = self.active, self.v, md.p, md.a, md.b, self.count
        duration = finish - start
        deleted = []
        for j in self.U:
            if j == i or not active[j][r]:
                continue
            slack = v[j][r] - p[j][r]
            # Intersection cannot exceed the occupation length. Equality fits.
            if slack >= duration or finish <= a[j] or start >= b[j]:
                continue
            left = start if start > a[j] else a[j]
            right = finish if finish < b[j] else b[j]
            if right - left > slack:
                if count[j] == 1:
                    return None
                deleted.append(j)
        return deleted
