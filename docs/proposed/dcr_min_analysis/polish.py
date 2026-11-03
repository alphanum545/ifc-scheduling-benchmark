"""DCR-Min-cost followed by a LOSS-style polish (analysis of a possible extension).

usage (repo root): python3 docs/proposed/dcr_min_analysis/polish.py SHARD SHARDS OUT.jsonl [--min-tasks 0] [--max-tasks 200]

Takes DCR-Min-cost's plan (task order and assignment) and applies the deadline-constrained LOSS
loop of baselines.py from there: repeatedly the cheaper reassignment with the smallest
(p_new - p_cur) / (c_cur - c_new), kept if the evaluated makespan still meets D.
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
from algorithms.dcr_min import DCRMinCostScheduler  # noqa: E402
from generator.schedule import build_schedule  # noqa: E402

shard, shards, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
arg = lambda k, d: int(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d  # noqa: E731
lo_t, hi_t = arg('--min-tasks', 0), arg('--max-tasks', 200)
man = json.load(open('manifests/dev-v1.json'))
bases = {b['base_instance_id']: b for b in man['base_entries']}
ents = sorted((e for e in man['entries'] if lo_t <= e['target_task_count'] <= hi_t), key=lambda e: e['instance_id'])
ents = ents[shard::shards]
done = {json.loads(x)['iid'] for x in open(out)} if Path(out).exists() else set()

with open(out, 'a') as f:
    for e in ents:
        if e['instance_id'] in done:
            continue
        base = json.load(open(Path('data/dev', bases[e['base_instance_id']]['path'])))
        qos = json.load(open(Path('data/dev', e['path'])))
        inp = AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split='development')
        md, D = Model.create(inp), inp.deadline_us
        t = time.perf_counter()
        dec = DCRMinCostScheduler().schedule(inp)
        t_dcr = time.perf_counter() - t
        order, asg = list(dec.task_order), dict(dec.resource_assignments)
        idx = {r: k for k, r in enumerate(md.resources)}
        n, m = len(md.tasks), len(md.resources)
        cur = [idx[asg[x]] for x in md.tasks]
        cost0 = cost = sum(md.c[i][cur[i]] for i in range(n))
        ms = build_schedule(base, task_order=order, resource_assignments=asg).schedule['makespan_us']
        ms0, evals, heap = ms, 1, []

        def push(i):
            for r in range(m):
                dc = md.c[i][cur[i]] - md.c[i][r]
                if dc > 0:
                    heapq.heappush(heap, (Fraction(md.p[i][r] - md.p[i][cur[i]], dc), i, r, cur[i]))
        if ms <= D:
            for i in range(n):
                push(i)
        while heap:
            _, i, r, was = heapq.heappop(heap)
            if cur[i] != was:
                continue
            asg[md.tasks[i]] = md.resources[r]
            new, evals = build_schedule(base, task_order=order, resource_assignments=asg).schedule['makespan_us'], evals + 1
            if new <= D:
                ms, cost, cur[i] = new, cost - md.c[i][was] + md.c[i][r], r
                push(i)
            else:
                asg[md.tasks[i]] = md.resources[was]
        f.write(json.dumps({'iid': e['instance_id'], 'qos': e['qos_profile'], 'tasks': e['target_task_count'], 'D': D,
                            'dcr_cost': cost0, 'dcr_ms': ms0, 'polished_cost': cost, 'polished_ms': ms, 'evals': evals,
                            't_dcr_s': t_dcr, 't_polish_s': time.perf_counter() - t - t_dcr}) + '\n')
        f.flush()
