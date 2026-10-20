import sys, json, time, hashlib
from pathlib import Path
DS=Path(sys.argv[1]); sys.path[:0]=[str(DS),'/usr/lib/python3/dist-packages']
from generator.config import load_config
from generator.materialize import selected_base_instance_id, build_qos_instance, _json_file_bytes, _safe_source
from generator.dax import normalize_dax
from generator.instance import build_base_instance
import generator.materialize as M
cfg=load_config(str(DS/'config/benchmark-v1.yaml'))
sel=json.loads((DS/'manifests/pilot-selection-v1.json').read_text())
man=json.load(open(sys.argv[2]))
want={e['instance_id']:e for e in man['entries']}; wantb={b['base_instance_id']:b for b in man['base_entries']}
ids=sys.argv[3:]
for cid in ids:
  s=[e for e in sel['entries'] if e['candidate_id']==cid][0]
  t=time.time()
  wf=normalize_dax(_safe_source(DS/'source_workflows',s['source_path']),family=s['family'],target_task_count=int(s['target_task_count']),replicate_id=s['replicate_id'],reference_mips=int(cfg['workflows']['reference_mips']))
  base=build_base_instance(wf,dict(cfg),scale=s['resource_scale'],scenario=s['scenario_profile'],seed=int(s['ifc_realization_seed']))
  bid=base['metadata']['base_instance_id']
  t1=time.time()
  cal=M.build_calibration_result(base,k=int(cfg['budget']['calibration']['tradeoff_solutions']))
  t2=time.time()
  q=build_qos_instance(s,cal,cfg)
  print(cid[-60:], 'base', hashlib.sha256(_json_file_bytes(base)).hexdigest()==wantb[bid]['sha256'], 'qos', hashlib.sha256(_json_file_bytes(q)).hexdigest()==want[cid]['sha256'], f'build {t1-t:.1f}s calib {t2-t1:.1f}s')
