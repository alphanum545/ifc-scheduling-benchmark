from copy import deepcopy
import random
from unittest.mock import patch

import pytest

from algorithms.dcr_ifc.model import Model
from algorithms.dcr_ifc.reserve import ReservePool as OriginalPool, dot
from algorithms.dcr_ifc_optimized.state import State
from algorithms.dcr_ifc_v1 import DCRV1Scheduler, DCRV1AdmissionScheduler
from algorithms.dcr_ifc_v1.reserve import ReservePool
from experiment.evaluator_adapter import evaluate_decision
from test_dcr_ifc import fixture, inp


def direct_bound(pool, state):
    if any(state.count[j] == 0 for j in state.U):
        return None
    return max(state.model.H * state.spent +
        sum(min(pool.weights[ell][j][q] for q in range(len(state.model.resources))
                if state.active[j][q]) for j in state.U) -
        sum(dot(z[q], state.K[q]) for q in range(len(z)))
        for ell, z in enumerate(pool.prices))


class OraclePool(ReservePool):
    """Slow independent full-domain recomputation after actual commit."""
    def prepare(self, state, i, placements, deletions):
        self.expected = {}
        for r, deleted in deletions.items():
            s, f = placements[r]
            after = deepcopy(state)
            after.commit(i, r, s, f)
            bound = direct_bound(self, after)
            self.expected[r] = None if bound is None else (
                OriginalPool.after_candidate(self, state, i, r, s, f, deleted), bound)

    def candidate_bounds(self, state, i, r, start, finish, deleted):
        return self.expected[r]


def random_input(case, n=8, m=7):
    rng = random.Random(318711 + case)
    return inp(fixture([[rng.randint(1, 18) for _ in range(m)] for _ in range(n)],
        [[rng.randint(0, 12) for _ in range(m)] for _ in range(n)],
        [(i,j) for i in range(n) for j in range(i+1,n) if rng.random() < .3],
        tiers=[rng.choice(['iot','fog','cloud']) for _ in range(m)],
        bits=rng.choice([0,1,50,1000])), rng.randint(5,110), rng.randint(0,100))


@pytest.mark.parametrize('case',range(120))
def test_batched_bounds_equal_independent_postcommit_domains(case):
    rng = random.Random(case)
    st = State(Model.create(random_input(case)))
    pool = None
    while st.U and all(st.count[j] for j in st.U):
        if pool is None or len(st.order) in st.model.epochs:
            pool = ReservePool(st)
        pool.refresh_minima(st)
        i = st.choose_task()
        positions = [st.insertion(i,r) for r in range(len(st.model.resources))]
        candidates = {}
        for r,(s,f) in enumerate(positions):
            if st.active[i][r] and f <= st.model.b[i]:
                deleted = st.capacity_deletions(i,r,s,f)
                if deleted is not None:
                    candidates[r] = deleted
        pool.prepare(st,i,positions,candidates)
        for r,deleted in candidates.items():
            s,f = positions[r]
            after = deepcopy(st)
            after.commit(i,r,s,f)
            bound = direct_bound(pool,after)
            observed = pool.candidate_bounds(st,i,r,s,f,deleted)
            assert (observed is None) == (bound is None)
            assert st.children_fit(i,r,s,f) == (bound is not None)
            if bound is not None:
                assert observed == (OriginalPool.after_candidate(pool,st,i,r,s,f,deleted),bound)
        r = rng.randrange(len(positions))
        st.commit(i,r,*positions[r])


@pytest.mark.parametrize('case',range(160))
@pytest.mark.parametrize('scheduler',[DCRV1Scheduler,DCRV1AdmissionScheduler])
def test_full_policy_matches_slow_oracle_and_authoritative_evaluator(case,scheduler):
    input_ = random_input(case, n=1+case%8, m=1+case%7)
    before = deepcopy(input_.instance)
    actual = scheduler().schedule(input_)
    with patch('algorithms.dcr_ifc_v1.scheduler.ReservePool', OraclePool):
        expected = scheduler().schedule(input_)
    assert actual == expected
    assert input_.instance == before
    ev = evaluate_decision(input_,actual)
    if not actual.internal_statistics['input_budget_lower_bound_exceeds_budget']:
        assert ev.budget_feasible
        if actual.internal_statistics['first_fallback_step'] is None:
            assert ev.joint_feasible


def test_exact_equality_zero_budget_and_seed_guard():
    for cls in (DCRV1Scheduler,DCRV1AdmissionScheduler):
        for deadline in (1,2,3,4,10):
            input_ = inp(fixture([[deadline]],[[0]]),deadline,0)
            assert evaluate_decision(input_,cls().schedule(input_)).joint_feasible
        with pytest.raises(ValueError):
            cls().schedule(input_,seed=1)


def test_packing_negative_control_remains_an_incomplete_certificate():
    input_ = inp(fixture([[1,1,4],[3,2,2],[3,2,2],[3,2,2],[1,1,1]],[[0,0,0]]*5,[(0,4)]),3,0)
    decision = DCRV1Scheduler().schedule(input_)
    assert decision.internal_statistics['admission_is_completion_certificate'] is False
    assert decision.internal_statistics['first_fallback_step'] is not None
    assert not evaluate_decision(input_,decision).joint_feasible
