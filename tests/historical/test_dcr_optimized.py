from copy import deepcopy
import random

import pytest

from algorithms.dcr_ifc import DCRScheduler
from algorithms.dcr_ifc.model import Model
from algorithms.dcr_ifc.reserve import ReservePool as ReferencePool
from algorithms.dcr_ifc.state import State as ReferenceState
from algorithms.dcr_ifc_optimized import DCROptimizedScheduler
from algorithms.dcr_ifc_optimized.reserve import ReservePool
from algorithms.dcr_ifc_optimized.state import State
from test_dcr_ifc import fixture, inp, brute_oracle


@pytest.mark.parametrize('case', range(180))
def test_complete_decision_and_statistics_equal_reference_and_oracle(case):
    rng = random.Random(99401 + case)
    n, m = rng.randrange(1, 8), rng.randrange(1, 6)
    p = [[rng.randrange(1, 17) for _ in range(m)] for _ in range(n)]
    c = [[rng.randrange(0, 13) for _ in range(m)] for _ in range(n)]
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < .23]
    input_ = inp(fixture(p, c, edges, bits=rng.choice([0, 1, 25])),
                 D=rng.randrange(1, 90), B=rng.randrange(0, 100))
    before = deepcopy(input_.instance)
    optimized = DCROptimizedScheduler().schedule(input_)
    assert optimized == DCRScheduler().schedule(input_)
    order, mapping, _ = brute_oracle(input_)
    assert (optimized.task_order, optimized.resource_assignments) == (order, mapping)
    assert input_.instance == before


@pytest.mark.parametrize('case', range(30))
def test_incremental_totals_and_capacity_screen_match_full_recomputation(case):
    rng = random.Random(18071 + case)
    n, m = 12, 6
    md = Model.create(inp(fixture(
        [[rng.randint(1, 20) for _ in range(m)] for _ in range(n)],
        [[rng.randint(0, 20) for _ in range(m)] for _ in range(n)],
        [(i, i + 3) for i in range(n - 3)], bits=25), 80, 100))
    st = State(md)
    pool = reference_pool = None
    while st.U and all(st.count[j] for j in st.U):
        if pool is None or len(st.order) in md.epochs:
            pool, reference_pool = ReservePool(st), ReferencePool(st)
        reference_pool.refresh_minima(st)
        pool.refresh_minima(st)
        assert pool.minimum == reference_pool.minimum
        assert pool.totals == reference_pool.totals
        assert pool.current == reference_pool.current
        # An idempotent refresh must not double-count a commit or a deletion.
        pool.refresh_minima(st)
        assert pool.totals == reference_pool.totals
        i = st.choose_task()
        for r in range(m):
            s, f = st.insertion(i, r)
            expected = ReferenceState.capacity_deletions(st, i, r, s, f)
            assert st.capacity_deletions(i, r, s, f) == expected
            if expected is not None and st.active[i][r] and f <= md.b[i]:
                assert pool.after_candidate(st, i, r, s, f, expected) == reference_pool.after_candidate(st, i, r, s, f, expected)
        r = rng.randrange(m)
        s, f = st.insertion(i, r)
        st.commit(i, r, s, f)


def test_exact_capacity_equality_and_tiny_zero_budget():
    for D in (1, 2, 3, 4, 10):
        input_ = inp(fixture([[D]], [[0]]), D, 0)
        assert DCROptimizedScheduler().schedule(input_) == DCRScheduler().schedule(input_)
    md = Model.create(inp(fixture([[2, 2], [3, 3]], [[0, 0], [0, 0]]), 5, 0))
    st = State(md)
    assert st.capacity_deletions(0, 0, 0, 2) == []
    assert st.capacity_deletions(0, 0, 0, 3) == [1]


def test_distinct_version_and_seed_rejection():
    assert DCROptimizedScheduler.algorithm_id != DCRScheduler.algorithm_id
    assert DCROptimizedScheduler.algorithm_version != DCRScheduler.algorithm_version
    with pytest.raises(ValueError):
        DCROptimizedScheduler().schedule(inp(fixture([[1]], [[0]])), seed=1)
