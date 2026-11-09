"""IC-PCP (Abrishami, Naghibzadeh, Epema, FGCS 29(1), 2013) on the fixed IFC v1 model (paper 2 comparator).

Audit and every adaptation decision: docs/paper_audits/ICPCP_2013.md (MAJOR MODEL ADAPTATION).
Kept: EST/EFT/LFT with minimum execution times (Eqs. 1-3), critical parent, partial critical paths, the
recursive AssignParents procedure (Algorithm 2), and AssignPath (Algorithm 3): the whole path goes on the one
resource with the lowest cost on which every path task finishes by its LFT, with zero transfer time inside
the path. Removed (not representable on a fixed pool): launching instances, interval billing and the
"extra time of the last interval" rule, and shifting already-scheduled children forward.
If no resource is applicable (on the paper's elastic model a new fastest instance always is), the path goes
on the resource that minimizes the largest LFT overrun (ties: cost, resource id).
Communication: exact route time when both endpoints are known (0 on the same resource), otherwise the pinned
route-aware average, as in the other ports.
"""
from __future__ import annotations

import heapq
import sys
from fractions import Fraction

from generator.reference_schedulers import _communication_metrics, _graph, _upward_ranks

from algorithms.common.interface import AlgorithmDecision, AlgorithmInput


class ICPCPScheduler:
    algorithm_id = "icpcp_ifc"
    algorithm_version = "icpcp_ifc_audit_20261109_impl1"

    def schedule(self, scheduling_input: AlgorithmInput, *, seed: int | None = None) -> AlgorithmDecision:
        inst = scheduling_input.instance
        g = _graph(inst)
        _, _, avg = _upward_ranks(inst, g)
        D = scheduling_input.deadline_us
        R = list(g.resource_ids)
        exe = {t: {r: int(v) for r, v in row.items()} for t, row in inst["execution_time_us"].items()}
        cost = {t: {r: int(v) for r, v in row.items()} for t, row in inst["compute_cost_ncu"].items()}
        met = {t: min(exe[t].values()) for t in g.task_ids}
        topo = list(g.topological_order)
        exact_cache: dict = {}

        def exact(p, c, rp, rc):
            if rp == rc:
                return 0
            key = (p, c, rp, rc)
            if key not in exact_cache:
                exact_cache[key] = _communication_metrics(inst, g, parent=p, child=c, source_resource=rp,
                                                          target_resource=rc)["communication_time_us"]
            return exact_cache[key]

        res: dict[str, str] = {}
        ast: dict[str, int] = {}
        aft: dict[str, int] = {}
        cal: dict[str, list[tuple[int, int]]] = {r: [] for r in R}
        est: dict[str, Fraction] = {}
        lft: dict[str, Fraction] = {}

        def comm_known(p, c):  # transfer estimate with whatever is known about the endpoints
            if p in res and c in res:
                return exact(p, c, res[p], res[c])
            return avg[f"{p}->{c}"]

        def refresh():
            for t in topo:
                if t in res:
                    continue
                e = Fraction(0)
                for p in g.parents[t]:
                    e = max(e, (aft[p] if p in res else est[p] + met[p]) + comm_known(p, t))
                est[t] = e
            for t in reversed(topo):
                if t in res:
                    continue
                l = Fraction(D)
                for c in g.children[t]:
                    l = min(l, (ast[c] if c in res else lft[c] - met[c]) - comm_known(t, c))
                lft[t] = l

        def eft(t):
            return aft[t] if t in res else est[t] + met[t]

        def critical_parent(t):
            cands = [p for p in g.parents[t] if p not in res]
            if not cands:
                return None
            return max(cands, key=lambda p: (eft(p) + comm_known(p, t), p))

        def try_path(path, r):
            """Place path consecutively on r (insertion into idle gaps). Returns (overrun, cost, starts)."""
            intervals = list(cal[r])
            starts, ends, overrun = {}, {}, None
            inpath = set(path)
            prev_end = 0
            for t in path:
                ready = Fraction(0)
                for p in g.parents[t]:
                    if p in ends:
                        ready = max(ready, ends[p])
                    elif p in res:
                        ready = max(ready, aft[p] + exact(p, t, res[p], r))
                    else:
                        ready = max(ready, est[p] + met[p] + avg[f"{p}->{t}"])
                limit = Fraction(D)
                for c in g.children[t]:
                    if c in inpath:
                        continue  # checked through the child's own start
                    if c in res:
                        limit = min(limit, ast[c] - exact(t, c, r, res[c]))
                    else:
                        limit = min(limit, lft[c] - met[c] - avg[f"{t}->{c}"])
                dur = exe[t][r]
                ready = Fraction(ready)
                start = max(-(-ready.numerator // ready.denominator), prev_end)  # integer microseconds
                pos = len(intervals)
                for k, (s, e) in enumerate(intervals):
                    if start + dur <= s:
                        pos = k
                        break
                    if start < e:
                        start = e
                intervals.insert(pos, (start, start + dur))
                starts[t], ends[t] = start, start + dur
                prev_end = start + dur
                over = start + dur - limit
                overrun = over if overrun is None else max(overrun, over)
            return overrun, sum(cost[t][r] for t in path), starts

        stats = {"paths": 0, "fallback_paths": 0}

        def assign_path(path):
            best_ok, best_fb = None, None
            for r in R:
                over, c, starts = try_path(path, r)
                if over <= 0:
                    if best_ok is None or (c, max(starts.values()), r) < best_ok[0]:
                        best_ok = ((c, max(starts.values()), r), r, starts)
                elif best_fb is None or (over, c, r) < best_fb[0]:
                    best_fb = ((over, c, r), r, starts)
            stats["paths"] += 1
            if best_ok is None:
                stats["fallback_paths"] += 1
            _, r, starts = best_ok if best_ok is not None else best_fb
            for t in path:
                res[t], ast[t], aft[t] = r, starts[t], starts[t] + exe[t][r]
                cal[r].append((ast[t], aft[t]))
            cal[r].sort()
            refresh()

        def assign_parents(t):
            while any(p not in res for p in g.parents[t]):
                path, ti = [], t
                while (cp := critical_parent(ti)) is not None:
                    path.insert(0, cp)
                    ti = cp
                assign_path(path)
                for ti in path:
                    assign_parents(ti)

        refresh()
        old = sys.getrecursionlimit()
        sys.setrecursionlimit(max(old, 10 * len(topo) + 1000))
        try:
            # Dummy exit node with AST = D: its parents are the real exit tasks (Algorithm 1, lines 3-7).
            while any(t not in res for t in topo):
                sinks = [t for t in topo if not g.children[t] and t not in res]
                exit_parent = max(sinks, key=lambda t: (eft(t), t))
                path, ti = [exit_parent], exit_parent
                while (cp := critical_parent(ti)) is not None:
                    path.insert(0, cp)
                    ti = cp
                assign_path(path)
                for ti in path:
                    assign_parents(ti)
        finally:
            sys.setrecursionlimit(old)

        # Evaluation order: topological, earliest internal start first.
        indeg = {t: len(g.parents[t]) for t in topo}
        pos = {t: k for k, t in enumerate(topo)}
        heap = [(ast[t], pos[t], t) for t in topo if indeg[t] == 0]
        heapq.heapify(heap)
        order = []
        while heap:
            _, _, t = heapq.heappop(heap)
            order.append(t)
            for c in g.children[t]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    heapq.heappush(heap, (ast[c], pos[c], c))
        stats["internal_makespan_us"] = max(aft.values())
        stats["internal_compute_cost_ncu"] = sum(cost[t][r] for t, r in res.items())
        return AlgorithmDecision(tuple(order), dict(res), stats)
