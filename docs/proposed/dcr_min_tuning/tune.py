"""Tuning grid: oracle x strategy for DCR-Min on small dev instances.

usage: python3 tune.py SHARD SHARDS OUT.jsonl
"""
import json, sys, time
sys.path.insert(0, '.')
from pathlib import Path
from algorithms.common.interface import AlgorithmInput
from algorithms.dcr_min import DCRMinCostScheduler, DCRMinMakespanScheduler
from algorithms.dcr_ifc_v4 import DCRV4QualityScheduler
from algorithms.dcr_ifc_v1 import DCRV1AdmissionScheduler
from algorithms.dcr_ifc_v4_rescue import DCRV4RescueScheduler
from generator.schedule import build_schedule

shard, shards, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
m = json.load(open('manifests/dev-v1.json'))
bases = {b['base_instance_id']: b for b in m['base_entries']}
ents = sorted((e for e in m['entries'] if e['target_task_count'] <= 200), key=lambda e: e['instance_id'])
ents = ents[::2][shard::shards]   # every second small instance, stratified by sorted id
ORACLES = {'v4': DCRV4QualityScheduler, 'v1adm': DCRV1AdmissionScheduler, 'v4r': DCRV4RescueScheduler}
done = set()
if Path(out).exists():
    done = {(r['iid'], r['cfg']) for r in map(json.loads, open(out))}
f = open(out, 'a')
for e in ents:
    base = json.load(open(Path('data/dev', bases[e['base_instance_id']]['path'])))
    qos = json.load(open(Path('data/dev', e['path'])))
    inp = AlgorithmInput.from_artifacts(base_instance=base, qos_instance=qos, split='development')
    ref = {'t_fast': qos['deadline']['t_fast_us'], 'cost_floor': qos['budget']['cost_floor_ref_ncu'],
           'w_ms': qos['joint_feasibility_witness']['makespan_us'], 'w_cost': qos['joint_feasibility_witness']['compute_cost_ncu']}
    cfgs = [('base', 'v4r', None, None)]
    for on in ORACLES:
        for strat in ('bisect', 'descent', 'hybrid'):
            cfgs += [('mk', on, strat, DCRMinMakespanScheduler), ('cost', on, strat, DCRMinCostScheduler)]
    for kind, on, strat, cls in cfgs:
        cfg = f'{kind}:{on}:{strat}'
        if (e['instance_id'], cfg) in done:
            continue
        sch = DCRV4RescueScheduler() if kind == 'base' else cls(ORACLES[on](), strategy=strat)
        t = time.perf_counter(); d = sch.schedule(inp); rt = time.perf_counter() - t
        s = build_schedule(base, task_order=d.task_order, resource_assignments=d.resource_assignments,
                           deadline_us=inp.deadline_us, budget_ncu=inp.budget_ncu).schedule
        st = d.internal_statistics
        f.write(json.dumps({'iid': e['instance_id'], 'cfg': cfg, 'qos': e['qos_profile'], 'family': e['family'],
                            'tasks': e['target_task_count'], 'ms': s['makespan_us'], 'cost': s['compute_cost_ncu'],
                            'D': inp.deadline_us, 'B': inp.budget_ncu, 'agree': s['makespan_us'] == st.get('internal_makespan_us'),
                            'probes': len(st.get('dcrmin_probes', [])), 'status': st.get('dcrmin_status'), 'rt': rt, **ref}) + '\n')
        f.flush()
    print('done', e['instance_id'], flush=True)
