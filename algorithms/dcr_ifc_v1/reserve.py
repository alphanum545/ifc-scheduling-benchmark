"""Exact child-arrival reserve via batched three-tier threshold sweeps."""
from algorithms.dcr_ifc.model import TIERS, overlap
from algorithms.dcr_ifc.reserve import dot
from algorithms.dcr_ifc_optimized.reserve import ReservePool as CapacityPool


class ReservePool(CapacityPool):
    def prepare(self, state, i, placements, deletions):
        """Prepare all locally admissible candidates in O(outdegree(i) * m).

        Candidate sorting is once per parent; duration orders already belong to
        the monotone state. The fixed three tiers and price vectors are constants.
        Only the candidate resource can lose a capacity option, handled separately.
        """
        md = state.model
        self.arrival_delta = {r: [0, 0, 0] for r in deletions}
        self.empty = set()
        groups = {tier: sorted((r for r in deletions if md.tiers[r] == tier),
                               key=lambda r: (-placements[r][1], r)) for tier in TIERS}
        deleted_sets = {r: set(js) for r, js in deletions.items()}
        for j in md.children[i]:
            best = {r: [None, None, None] for r in deletions}
            for srcs in groups.values():
                if not srcs:
                    continue
                src = srcs[0]
                for tier in TIERS:
                    targets = state.tier_choices[j][tier].ordered
                    # A distinct exemplar establishes the fixed tier-pair delay.
                    dst = next((q for q in targets[:2] if q != src), None)
                    if dst is None:
                        continue
                    delay = md.delay(i, j, src, dst)
                    first, second = [None] * 3, [None] * 3
                    cursor = 0
                    for r in srcs:
                        threshold = md.b[j] - placements[r][1] - delay
                        while cursor < len(targets) and md.p[j][targets[cursor]] <= threshold:
                            q = targets[cursor]
                            cursor += 1
                            if not state.active[j][q]:
                                continue
                            for ell in range(3):
                                key = (self.weights[ell][j][q], md.p[j][q], q)
                                if first[ell] is None or key < first[ell]:
                                    second[ell], first[ell] = first[ell], key
                                elif second[ell] is None or key < second[ell]:
                                    second[ell] = key
                        for ell in range(3):
                            choice = first[ell]
                            if choice is not None and choice[2] == r:
                                choice = second[ell]
                            if choice is not None and (best[r][ell] is None or choice[0] < best[r][ell]):
                                best[r][ell] = choice[0]
            for r in deletions:
                # Same resource has zero communication, but must survive capacity pruning.
                if (state.active[j][r] and j not in deleted_sets[r] and
                        placements[r][1] + md.p[j][r] <= md.b[j]):
                    for ell in range(3):
                        weight = self.weights[ell][j][r]
                        if best[r][ell] is None or weight < best[r][ell]:
                            best[r][ell] = weight
                if best[r][0] is None:
                    self.empty.add(r)
                    continue
                for ell in range(3):
                    self.arrival_delta[r][ell] += best[r][ell] - self.weights[ell][j][self.minimum[ell][j][0]]
        self.child_set = set(md.children[i])

    def candidate_bounds(self, state, i, r, start, finish, deleted):
        """Return (capacity-only, actual-arrival) bounds, or None for no child option."""
        if r in self.empty:
            return None
        md = state.model
        occupation = tuple(overlap(start, finish, 0, theta) for theta in md.theta)
        capacity, arrival = [], []
        for ell, z in enumerate(self.prices):
            w, mins = self.weights[ell], self.minimum[ell]
            base = self.totals[ell] + md.H * md.c[i][r] - w[i][mins[i][0]] + dot(z[r], occupation)
            old, new = base, base + self.arrival_delta[r][ell]
            for j in deleted:
                first, second = mins[j]
                if first == r:
                    if second is None:
                        raise ArithmeticError('candidate removes the only capacity option')
                    delta = w[j][second] - w[j][first]
                    old += delta
                    if j not in self.child_set:
                        new += delta
            capacity.append(old)
            arrival.append(new)
        old, new = max(capacity), max(arrival)
        if not self.current <= old <= new:
            raise ArithmeticError('reserve monotonicity violated')
        return old, new
