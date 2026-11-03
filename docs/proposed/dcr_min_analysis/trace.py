"""Probe traces and dense oracle sweeps for DCR-Min (analysis only).

usage (repo root): python3 docs/proposed/dcr_min_analysis/trace.py SHARD SHARDS OUT.jsonl [--max-tasks 200] [--only INSTANCE_ID]

Per instance (dev, sorted by id, <= max-tasks):
  * trace: each DCR-Min variant run with max_probes=24 (the first 12 probes are identical to the
    default run, since both searches are prefix-deterministic); every probe is logged.
  * sweep: the oracle (DCR-v4R) run at 40 log-spaced targets, an upper reference for what any
    search over the same single knob could find.
  * ablations: makespan without the 2x slack start probe; cost with the instance budget B added
    as a warm-start probe (B is not part of the pure min-cost problem, so this is diagnostic only).
"""
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, '.')
from dataclasses import replace  # noqa: E402

from algorithms.common.interface import AlgorithmInput  # noqa: E402
from algorithms.dcr_ifc_v4_rescue import DCRV4RescueScheduler  # noqa: E402
from algorithms.dcr_min import DCRMinCostScheduler, DCRMinMakespanScheduler, lower_bounds  # noqa: E402

shard, shards, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
max_tasks = int(sys.argv[sys.argv.index('--max-tasks') + 1]) if '--max-tasks' in sys.argv else 200
m = json.load(open('manifests/dev-v1.json'))
bases = {b['base_instance_id']: b for b in m['base_entries']}
only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
ents = sorted((e for e in m['entries'] if e['target_task_count'] <= max_tasks and (only is None or e['instance_id'] == only)),
              key=lambda e: e['instance_id'])
ents = ents[shard::shards]
done = {json.loads(x)['iid'] for x in open(out)} if Path(out).exists() else set()
oracle = DCRV4RescueScheduler()


def probe(inp, **kw):
    st = oracle.schedule(replace(inp, **kw)).internal_statistics
    return st['internal_makespan_us'], st['internal_compute_cost_ncu']


def logspace(a, b, k):
    a = max(1, a)
    return sorted({int(round(math.exp(math.log(a) + (math.log(b) - math.log(a)) * j / (k - 1)))) for j in range(k)})


with open(out, 'a') as f:
    for e in ents:
        if e['instance_id'] in done:
            continue
        base = json.load(open(Path('data/dev', bases[e['base_instance_id']]['path'])))
        qos = json.load(open(Path('data/dev', e['path'])))
        inp = AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split='development')
        lb = lower_bounds(inp)
        rec = {'iid': e['instance_id'], 'family': e['family'], 'tasks': e['target_task_count'], 'qos': e['qos_profile'],
               'D': inp.deadline_us, 'B': inp.budget_ncu, 'lb': lb,
               't_fast': qos['deadline']['t_fast_us'], 'cost_floor': qos['budget']['cost_floor_ref_ncu']}
        t = time.perf_counter()
        rec['mk_trace'] = DCRMinMakespanScheduler(max_probes=24).schedule(inp).internal_statistics['dcrmin_probes']
        rec['cost_trace'] = DCRMinCostScheduler(max_probes=24).schedule(inp).internal_statistics['dcrmin_probes']
        rec['t_trace'] = time.perf_counter() - t
        ms0 = rec['mk_trace'][0]['makespan_us']
        t = time.perf_counter()
        rec['mk_sweep'] = [{'deadline_us': d, 'makespan_us': r[0], 'cost_ncu': r[1]}
                           for d in logspace(lb['makespan_lb_us'], 2 * ms0, 40) for r in [probe(inp, deadline_us=d)]]
        lo = lb['cost_lb_deadline_ncu'] or 0
        rec['cost_sweep'] = [{'budget_ncu': b, 'makespan_us': r[0], 'cost_ncu': r[1]}
                             for b in sorted({lo} | set(logspace(max(lo, lb['cost_max_ncu'] // 10000), lb['cost_max_ncu'], 40)))
                             for r in [probe(inp, budget_ncu=b)]]
        rec['t_sweep'] = time.perf_counter() - t
        # ablation 1: makespan search without the 2x slack start probe (descent from the LB_T plan)
        a1 = DCRMinMakespanScheduler()
        r = probe(inp, deadline_us=lb['makespan_lb_us'])
        log, best = [{'deadline_us': lb['makespan_lb_us'], 'makespan_us': r[0], 'cost_ncu': r[1]}], [r[0]]

        def run(d):
            ms, c = probe(inp, deadline_us=d)
            log.append({'deadline_us': d, 'makespan_us': ms, 'cost_ncu': c})
            imp = c <= inp.budget_ncu and ms < best[0]
            if imp:
                best[0] = ms
            return imp, c <= inp.budget_ncu and ms <= d
        a1._search(lb['makespan_lb_us'], lambda: best[0], run, log)
        rec['abl_mk_noslack'] = best[0]
        # ablation 2: cost search with the instance budget as an extra first probe
        ms, c = probe(inp, budget_ncu=inp.budget_ncu)
        rec['abl_cost_warmB'] = {'makespan_us': ms, 'cost_ncu': c}
        f.write(json.dumps(rec) + '\n')
        f.flush()
        print('done', e['instance_id'], f"{rec['t_trace']:.1f}s {rec['t_sweep']:.1f}s", flush=True)
