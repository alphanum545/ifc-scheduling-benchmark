"""Classic greedy minimisation baselines (Sakellariou et al., 2007), for comparison with DCR-Min.

usage (repo root): python3 docs/proposed/dcr_min_analysis/baselines.py SHARD SHARDS OUT.jsonl [--min-tasks 0] [--max-tasks 200]

  GAIN  (min makespan s.t. cost <= B): start from the cheapest assignment (ties: faster); then
        repeatedly take the reassignment with the largest time gain per extra cost,
        (p_cur - p_new) / (c_new - c_cur), accept it if the budget still holds and the
        evaluated makespan does not get worse.
  LOSS  (min cost s.t. makespan <= D): start from the HEFT-IFC schedule; then repeatedly take
        the reassignment with the smallest time loss per cost saved,
        (p_new - p_cur) / (c_cur - c_new), accept it if the evaluated makespan still meets D.

Both evaluate every candidate move with the pinned Dataset evaluator (build_schedule), so they
are "evaluator-in-the-loop" baselines; DCR-Min never calls the evaluator. Task order is fixed
(GAIN: upward rank on pmin; LOSS: HEFT-IFC's own order).
"""
import heapq
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, '.')
from algorithms.common.interface import AlgorithmInput  # noqa: E402
from algorithms.dcr_ifc.model import Model  # noqa: E402
from algorithms.heft_ifc import HeftIFCScheduler  # noqa: E402
from generator.schedule import build_schedule  # noqa: E402

shard, shards, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
max_tasks = int(sys.argv[sys.argv.index('--max-tasks') + 1]) if '--max-tasks' in sys.argv else 200
man = json.load(open('manifests/dev-v1.json'))
bases = {b['base_instance_id']: b for b in man['base_entries']}
min_tasks = int(sys.argv[sys.argv.index('--min-tasks') + 1]) if '--min-tasks' in sys.argv else 0
ents = sorted((e for e in man['entries'] if min_tasks <= e['target_task_count'] <= max_tasks), key=lambda e: e['instance_id'])
ents = ents[shard::shards]
done = {json.loads(x)['iid'] for x in open(out)} if Path(out).exists() else set()


def evaluate(base, order, asg):
    return build_schedule(base, task_order=order, resource_assignments=asg).schedule['makespan_us']


def gain(base, md, B):
    n, m = len(md.tasks), len(md.resources)
    order = [md.tasks[i] for i in sorted(range(n), key=lambda i: -(md.h[i] + md.pmin[i]))]
    cur = [min(range(m), key=lambda r: (md.c[i][r], md.p[i][r], r)) for i in range(n)]
    cost = sum(md.c[i][cur[i]] for i in range(n))
    asg = {md.tasks[i]: md.resources[cur[i]] for i in range(n)}
    ms, evals = evaluate(base, order, asg), 1
    heap = []

    def push(i):
        for r in range(m):
            dp, dc = md.p[i][cur[i]] - md.p[i][r], md.c[i][r] - md.c[i][cur[i]]
            if dp > 0 and dc > 0:
                heapq.heappush(heap, (-Fraction(dp, dc), i, r, cur[i]))
    for i in range(n):
        push(i)
    while heap:
        _, i, r, was = heapq.heappop(heap)
        if cur[i] != was or cost - md.c[i][was] + md.c[i][r] > B:
            continue
        asg[md.tasks[i]] = md.resources[r]
        new, evals = evaluate(base, order, asg), evals + 1
        if new <= ms:
            ms, cost, cur[i] = new, cost - md.c[i][was] + md.c[i][r], r
            push(i)
        else:
            asg[md.tasks[i]] = md.resources[was]
    return {'makespan_us': ms, 'cost_ncu': cost, 'evals': evals}


def loss(base, md, inp, D):
    n, m = len(md.tasks), len(md.resources)
    dec = HeftIFCScheduler().schedule(inp)
    order = list(dec.task_order)
    idx = {r: k for k, r in enumerate(md.resources)}
    cur = [idx[dec.resource_assignments[t]] for t in md.tasks]
    asg = dict(dec.resource_assignments)
    ms, evals = evaluate(base, order, asg), 1
    cost = sum(md.c[i][cur[i]] for i in range(n))
    if ms > D:
        return {'makespan_us': ms, 'cost_ncu': cost, 'evals': evals, 'start_misses_D': True}
    heap = []

    def push(i):
        for r in range(m):
            dp, dc = md.p[i][r] - md.p[i][cur[i]], md.c[i][cur[i]] - md.c[i][r]
            if dc > 0:
                heapq.heappush(heap, (Fraction(dp, dc), i, r, cur[i]))
    for i in range(n):
        push(i)
    while heap:
        _, i, r, was = heapq.heappop(heap)
        if cur[i] != was:
            continue
        asg[md.tasks[i]] = md.resources[r]
        new, evals = evaluate(base, order, asg), evals + 1
        if new <= D:
            ms, cost, cur[i] = new, cost - md.c[i][was] + md.c[i][r], r
            push(i)
        else:
            asg[md.tasks[i]] = md.resources[was]
    return {'makespan_us': ms, 'cost_ncu': cost, 'evals': evals, 'start_misses_D': False}


with open(out, 'a') as f:
    for e in ents:
        if e['instance_id'] in done:
            continue
        base = json.load(open(Path('data/dev', bases[e['base_instance_id']]['path'])))
        qos = json.load(open(Path('data/dev', e['path'])))
        inp = AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split='development')
        md = Model.create(inp)
        t = time.perf_counter(); g = gain(base, md, inp.budget_ncu); g['runtime_s'] = time.perf_counter() - t
        t = time.perf_counter(); lo = loss(base, md, inp, inp.deadline_us); lo['runtime_s'] = time.perf_counter() - t
        f.write(json.dumps({'iid': e['instance_id'], 'qos': e['qos_profile'], 'tasks': e['target_task_count'],
                            'gain': g, 'loss': lo}) + '\n')
        f.flush()
        print('done', e['instance_id'], f"gain {g['evals']} evals {g['runtime_s']:.1f}s, loss {lo['evals']} evals {lo['runtime_s']:.1f}s", flush=True)
