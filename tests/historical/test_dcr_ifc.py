from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import random

import pytest
from generator.canonical import canonical_json_bytes
from generator.network import resource_route_metrics
from generator.reference_schedulers import _graph
from algorithms.common.interface import AlgorithmContractError, AlgorithmInput
from algorithms.dcr_ifc import DCRScheduler
from algorithms.dcr_ifc.model import Model, overlap
from algorithms.dcr_ifc.state import State, MonotoneChoices
from algorithms.dcr_ifc.reserve import ReservePool
from algorithms.dcr_ifc.scheduler import loss
from algorithms.proposed_registry import proposed_registry
from algorithms.registry import stage8_registry
from experiment.evaluator_adapter import evaluate_decision
from experiment.development_runner import FROZEN_PRIMARY_COMPARATOR_IDS


def fixture(p, c, edges=(), tiers=None, bits=0):
    n, m = len(p), len(p[0])
    tasks = [f'T{i:02}' for i in range(n)]
    resources = [f'R{i:02}' for i in range(m)]
    tiers = tiers or [('iot', 'fog', 'cloud')[i % 3] for i in range(m)]
    names = ['iot_iot_different', 'fog_fog_different', 'cloud_cloud_different',
             'iot_fog', 'iot_cloud', 'fog_cloud']
    return {'metadata': {'base_instance_id': 'synthetic-dcr'},
        'tasks': [{'task_id': t} for t in tasks],
        'resources': [{'resource_id': r, 'tier': tier} for r, tier in zip(resources, tiers)],
        'dependencies': [{'parent': tasks[i], 'child': tasks[j], 'data_bits': bits} for i, j in edges],
        'network': {'segments': {'link': {'bandwidth_mbps': 50, 'latency_us': 1, 'energy_pj_per_bit': 2}},
                    'routes': {key: ['link'] for key in names}},
        'execution_time_us': {t: dict(zip(resources, row)) for t, row in zip(tasks, p)},
        'compute_cost_ncu': {t: dict(zip(resources, row)) for t, row in zip(tasks, c)},
        'compute_energy_nj': {t: {r: 10 * p[i][j] for j, r in enumerate(resources)} for i, t in enumerate(tasks)}}


def inp(base, D=20, B=10):
    return AlgorithmInput(base, 'dcr-test', 'development', D, B)


def brute_oracle(input_):
    """Independent Fraction-based formula implementation; intentionally slow.

    Rebuilds domains and future minima from calendars, with m scans per trial.
    Not an executable policy variant and never used for benchmark timing.
    """
    base, D, B = input_.instance, input_.deadline_us, input_.budget_ncu
    gr = _graph(base)
    ts, rs = sorted(gr.task_ids), sorted(gr.resource_ids)
    p, c = base['execution_time_us'], base['compute_cost_ncu']
    pmin = {t: min(p[t].values()) for t in ts}
    cmin = {t: min(c[t].values()) for t in ts}
    a, h = {}, {}
    for t in gr.topological_order:
        a[t] = max((a[j] + pmin[j] for j in gr.parents[t]), default=0)
    for t in reversed(gr.topological_order):
        h[t] = max((pmin[j] + h[j] for j in gr.children[t]), default=0)
    b = {t: D-h[t] for t in ts}
    cuts = sorted({D*k//4 for k in (1, 2, 3, 4)}-{0})
    epochs = {len(ts)*k//4 for k in (0, 1, 2, 3)}
    g = {(t, r): [max(0, p[t][r]-max(0, b[t]-x)) for x in cuts] for t in ts for r in rs}
    if sum(cmin.values()) > B:
        return tuple(gr.topological_order), {t: min(rs, key=lambda r: (c[t][r], p[t][r], r)) for t in ts}, None
    U, done, order, mapping = set(ts), {}, [], {}
    calendars = {r: [] for r in rs}
    spent, fallback, first_fallback = 0, False, None
    def ov(s, f, l, r):
        return max(0, min(f, r)-max(s, l))
    def comm(parent, child, source, target):
        return resource_route_metrics(base['network'], gr.resource_tiers, source_resource_id=source,
                target_resource_id=target, data_bits=gr.data_bits_by_edge[parent+'->'+child])['communication_time_us']
    while U:
        rho = {(t,r): max([a[t]]+[done[j][2]+comm(j,t,mapping[j],r) for j in gr.parents[t] if j in done]) for t in U for r in rs}
        v = {(t,r): b[t]-a[t]-sum(ov(s,f,a[t],b[t]) for s,f in calendars[r]) for t in U for r in rs}
        domains = {t: [r for r in rs if p[t][r]<=v[t,r] and rho[t,r]+p[t][r]<=b[t]] for t in U}
        ready = [t for t in U if all(j in done for j in gr.parents[t])]
        i = min(ready, key=lambda t: (b[t]-pmin[t],len(domains[t]),t))
        positions = {}
        for r in rs:
            s = rho[i,r]
            for left,right in sorted(calendars[r]):
                if s+p[i][r]<=left: break
                if s<right: s=right
            positions[r] = (s,s+p[i][r])
        allowed = [r for r in rs if spent+c[i][r]+sum(cmin[t] for t in U-{i})<=B]
        screened = []
        if not fallback and all(domains.values()):
            K = {r: [x-sum(ov(s,f,0,x) for s,f in calendars[r]) for x in cuts] for r in rs}
            if len(order) in epochs:
                prices = [{r:[Fraction(0)]*len(cuts) for r in rs}]
                for ell in (0,1):
                    z=prices[-1]
                    demand={r:[0]*len(cuts) for r in rs}
                    for t in sorted(U):
                        rr=min(domains[t],key=lambda r:(c[t][r]+sum(x*y for x,y in zip(z[r],g[t,r])),p[t][r],r))
                        demand[rr]=[x+y for x,y in zip(demand[rr],g[t,rr])]
                    alpha=Fraction(max(B,1),D*D*(ell+1))
                    prices.append({r:[max(0,x+alpha*(d-k)) for x,d,k in zip(z[r],demand[r],K[r])] for r in rs})
            current=[]
            for z in prices:
                current.append(spent+sum(min(c[t][r]+sum(x*y for x,y in zip(z[r],g[t,r])) for r in domains[t]) for t in U)
                               -sum(sum(x*y for x,y in zip(z[r],K[r])) for r in rs))
            G0=max(current)
            f0=min(f for s,f in positions.values());ST=b[i]-f0;SB=B-G0
            if ST>=0 and SB>=0:
                for r in allowed:
                    s,f=positions[r]
                    if r not in domains[i] or f>b[i]: continue
                    trial={t:[q for q in domains[t] if q!=r or p[t][q]<=v[t,q]-ov(s,f,a[t],b[t])] for t in U-{i}}
                    if any(not vals for vals in trial.values()): continue
                    if any(not any(f+comm(i,t,r,q)+p[t][q]<=b[t] for q in trial[t]) for t in gr.children[i]): continue
                    G=[]
                    for z in prices:
                        G.append(spent+c[i][r]+sum(min(c[t][q]+sum(x*y for x,y in zip(z[q],g[t,q])) for q in trial[t]) for t in trial)
                                 -sum(sum(x*y for x,y in zip(z[q],K[q])) for q in rs)
                                 +sum(x*ov(s,f,0,theta) for x,theta in zip(z[r],cuts)))
                    GG=max(G)
                    if GG>B: continue
                    PT=Fraction(f-f0,ST) if ST else Fraction(0)
                    PB=(GG-G0)/SB if SB else Fraction(0)
                    screened.append(((max(PT,PB),min(PT,PB),f,c[i][r],r),r))
        if screened:
            r=min(screened)[1]
        else:
            if first_fallback is None:first_fallback=len(order)+1
            fallback=True;r=min(allowed,key=lambda q:(positions[q][1],c[i][q],q))
        s,f=positions[r];done[i]=(r,s,f);mapping[i]=r;order.append(i);spent+=c[i][r]
        calendars[r].append((s,f));U.remove(i)
    return tuple(order),mapping,first_fallback


def check_parity(input_):
    before=canonical_json_bytes(dict(input_.instance))
    d=DCRScheduler().schedule(input_)
    ev=evaluate_decision(input_,d)
    assert before==canonical_json_bytes(dict(input_.instance))
    if not d.internal_statistics['input_budget_lower_bound_exceeds_budget']:
        assert ev.budget_feasible
        assert d.internal_statistics['planned_assignments_sha256']==sha256(canonical_json_bytes(ev.schedule['assignments'])).hexdigest()
        assert d.internal_statistics['internal_makespan_us']==ev.schedule['makespan_us']
        assert d.internal_statistics['internal_compute_cost_ncu']==ev.schedule['compute_cost_ncu']
        if not d.internal_statistics['fallback_task_count']:assert ev.joint_feasible
    assert d.internal_statistics['price_refresh_count']<=4
    assert d.internal_statistics['full_schedule_rebuilds_inside_policy']==0
    return d,ev


def test_two_task_reservation_example():
    input_=inp(fixture([[2,1],[10,1]],[[0,3],[0,10]]),D=10,B=3)
    d,ev=check_parity(input_)
    assert d.resource_assignments=={'T00':'R01','T01':'R00'}
    assert ev.joint_feasible and ev.schedule['makespan_us']==10 and ev.schedule['compute_cost_ncu']==3


@pytest.mark.parametrize('case',range(180))
def test_independent_oracle_matches_exact_full_policy(case):
    rng=random.Random(99401+case)
    n,m=rng.randrange(1,8),rng.randrange(1,6)
    p=[[rng.randrange(1,17) for r in range(m)] for i in range(n)]
    c=[[rng.randrange(0,13) for r in range(m)] for i in range(n)]
    edges=[(i,j) for i in range(n) for j in range(i+1,n) if rng.random()<.23]
    input_=inp(fixture(p,c,edges,bits=rng.choice([0,1,25])),D=rng.randrange(1,90),B=rng.randrange(0,100))
    decision,ev=check_parity(input_)
    order,mapping,first_fallback=brute_oracle(input_)
    assert decision.task_order==order
    assert decision.resource_assignments==mapping
    if not decision.internal_statistics['input_budget_lower_bound_exceeds_budget']:
        assert decision.internal_statistics['first_fallback_step']==first_fallback
        if first_fallback is not None:
            assert decision.internal_statistics['fallback_task_count']==n-first_fallback+1


def test_cache_retains_distinct_equal_score_options_and_monotone_deletions():
    c=MonotoneChoices([2,0,1,3]);active=[True]*4
    assert c.top2(active)==(2,0)
    active[2]=False;assert c.top2(active)==(0,1)
    active[1]=False;assert c.top2(active)==(0,3)
    active[0]=False;assert c.top2(active)==(3,None)
    active[3]=False;assert c.top2(active)==(None,None)


@pytest.mark.parametrize('case',range(30))
def test_candidate_bound_and_child_cache_match_direct_computation(case):
    rng=random.Random(917+case);n,m=5,6
    model=Model.create(inp(fixture([[rng.randint(1,8) for _ in range(m)] for _ in range(n)],
               [[rng.randint(0,7) for _ in range(m)] for _ in range(n)],[(0,2),(1,2),(2,3),(2,4)],bits=20),60,40))
    st=State(model)
    while st.U and all(st.count[j] for j in st.U):
        i=st.choose_task();pool=ReservePool(st);pool.refresh_minima(st)
        for r in range(m):
            s,f=st.insertion(i,r)
            if not st.active[i][r] or f>model.b[i]:continue
            dels=st.capacity_deletions(i,r,s,f)
            if dels is None:continue
            brute_fit=all(any(st.active[j][q] and (q!=r or model.p[j][q]<=st.v[j][q]-overlap(s,f,model.a[j],model.b[j]))
                             and f+model.delay(i,j,r,q)+model.p[j][q]<=model.b[j] for q in range(m)) for j in model.children[i])
            assert st.children_fit(i,r,s,f)==brute_fit
            bound=pool.after_candidate(st,i,r,s,f,dels)
            direct=[]
            for ell,z in enumerate(pool.prices):
                total=model.H*(st.spent+model.c[i][r])
                for j in st.U:
                    if j==i:continue
                    options=[q for q in range(m) if st.active[j][q] and not (q==r and j in dels)]
                    total+=min(pool.weights[ell][j][q] for q in options)
                total-=sum(sum(zz*kk for zz,kk in zip(z[q],st.K[q])) for q in range(m))
                total+=sum(zz*overlap(s,f,0,t) for zz,t in zip(z[r],model.theta))
                direct.append(total)
            assert bound==max(direct) and bound>=pool.current
        r=min(range(m),key=lambda r:(model.c[i][r],r));s,f=st.insertion(i,r);st.commit(i,r,s,f)


@pytest.mark.parametrize('D',[1,2,3,4,10])
def test_zero_budget_all_free_exact_boundary_and_tiny_deadline(D):
    decision,ev=check_parity(inp(fixture([[D]],[[0]]),D,0))
    assert ev.joint_feasible and decision.internal_statistics['fallback_task_count']==0
    assert decision.internal_statistics['checkpoint_count']==min(D,4)


def test_budget_lower_bound_exception_returns_complete_minimum_cost_mapping():
    d,ev=check_parity(inp(fixture([[1,2],[2,1]],[[5,6],[2,3]],[(0,1)]),D=10,B=6))
    assert d.internal_statistics['input_budget_lower_bound_exceeds_budget'] and not ev.budget_feasible
    assert ev.schedule['compute_cost_ncu']==7


def test_rejects_nonnull_seed_and_invalid_numeric_matrix():
    b=fixture([[1,2]],[[0,1]])
    with pytest.raises(AlgorithmContractError):DCRScheduler().schedule(inp(b),seed=1)
    b['execution_time_us']['T00']['R00']=True
    with pytest.raises(AlgorithmContractError):DCRScheduler().schedule(inp(b))


def test_repeat_and_permuted_public_input_order_are_deterministic():
    b=fixture([[3,2,1],[5,4,2],[2,3,1]],[[0,2,4],[0,2,5],[0,1,2]],[(0,2),(1,2)],bits=1)
    d,_=check_parity(inp(b))
    bb=deepcopy(b);bb['tasks'].reverse();bb['resources'].reverse();bb['dependencies'].reverse()
    assert DCRScheduler().schedule(inp(bb))==d
    assert DCRScheduler().schedule(inp(b))==d


def test_frozen_registry_remains_exactly_seven():
    assert stage8_registry().ids()==FROZEN_PRIMARY_COMPARATOR_IDS
    assert proposed_registry().ids()==('dcr_ifc_v0',)


def test_tier_model_rejects_unavailable_route():
    b=fixture([[1,2],[1,2]],[[0,1],[0,1]],[(0,1)],bits=1)
    b['network']['routes'].pop('iot_fog')
    with pytest.raises((KeyError,ValueError)):DCRScheduler().schedule(inp(b))


def test_negative_control_admission_does_not_certify_completion():
    # Specification section 14: commit T00 to first resource strands integral packing.
    b=fixture([[1,1,4],[3,2,2],[3,2,2],[3,2,2],[1,1,1]],[[0,0,0]]*5,[(0,4)])
    md=Model.create(inp(b,3,0));st=State(md);pool=ReservePool(st);pool.refresh_minima(st)
    s,f=st.insertion(0,0);deleted=st.capacity_deletions(0,0,s,f)
    assert deleted==[1,2,3]
    assert st.children_fit(0,0,s,f)
    assert pool.after_candidate(st,0,0,s,f,deleted)<=0
    d,ev=check_parity(inp(b,3,0))
    assert not ev.joint_feasible
    assert d.internal_statistics['admission_is_completion_certificate'] is False
    assert d.internal_statistics['fallback_task_count']>0


def test_exact_loss_rejects_invalid_screened_margins():
    assert loss(0,0)==0 and loss(1,2)==Fraction(1,2)
    for a,b in [(1,0),(-1,1),(2,1),(0,-1)]:
        with pytest.raises(ArithmeticError):loss(a,b)
