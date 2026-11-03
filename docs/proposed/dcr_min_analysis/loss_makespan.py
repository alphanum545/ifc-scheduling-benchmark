"""LOSS1 (Sakellariou et al., 2007) for min makespan s.t. cost <= B, for comparison with DCR-Min.

usage (repo root): python3 docs/proposed/dcr_min_analysis/loss_makespan.py SHARD SHARDS OUT.jsonl

Start from the HEFT-IFC schedule. While its cost exceeds B, apply the reassignment with the
smallest LossWeight = (p_new - p_cur) / (c_cur - c_new) over all tasks and cheaper resources
(weights recomputed for the moved task only). Task order: HEFT-IFC's own. One Dataset evaluation
at the end. All dev instances.
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
man = json.load(open('manifests/dev-v1.json'))
bases = {b['base_instance_id']: b for b in man['base_entries']}
ents = sorted(man['entries'], key=lambda e: e['instance_id'])[shard::shards]
done = {json.loads(x)['iid'] for x in open(out)} if Path(out).exists() else set()

with open(out, 'a') as f:
    for e in ents:
        if e['instance_id'] in done:
            continue
        base = json.load(open(Path('data/dev', bases[e['base_instance_id']]['path'])))
        qos = json.load(open(Path('data/dev', e['path'])))
        inp = AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split='development')
        md = Model.create(inp)
        t = time.perf_counter()
        dec = HeftIFCScheduler().schedule(inp)
        n, m = len(md.tasks), len(md.resources)
        idx = {r: k for k, r in enumerate(md.resources)}
        cur = [idx[dec.resource_assignments[x]] for x in md.tasks]
        cost = sum(md.c[i][cur[i]] for i in range(n))
        heap, moves = [], 0

        def push(i):
            for r in range(m):
                dc = md.c[i][cur[i]] - md.c[i][r]
                if dc > 0:
                    heapq.heappush(heap, (Fraction(md.p[i][r] - md.p[i][cur[i]], dc), i, r, cur[i]))
        for i in range(n):
            push(i)
        while cost > inp.budget_ncu and heap:
            _, i, r, was = heapq.heappop(heap)
            if cur[i] != was:
                continue
            cost, cur[i], moves = cost - md.c[i][was] + md.c[i][r], r, moves + 1
            push(i)
        asg = {md.tasks[i]: md.resources[cur[i]] for i in range(n)}
        ms = build_schedule(base, task_order=list(dec.task_order), resource_assignments=asg).schedule['makespan_us']
        f.write(json.dumps({'iid': e['instance_id'], 'qos': e['qos_profile'], 'tasks': e['target_task_count'],
                            'makespan_us': ms, 'cost_ncu': cost, 'B': inp.budget_ncu, 'moves': moves,
                            'runtime_s': time.perf_counter() - t}) + '\n')
        f.flush()
