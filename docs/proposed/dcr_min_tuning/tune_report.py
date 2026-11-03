# usage (repo root): python3 docs/proposed/dcr_min_tuning/tune_report.py 'docs/proposed/dcr_min_tuning/grid-*.jsonl'
import json, glob, math, sys, statistics
from collections import defaultdict
S = sys.argv[1]
rows = [json.loads(l) for p in (glob.glob(f'{S}/tune-*.jsonl') or glob.glob(S)) for l in open(p)]
by = defaultdict(dict)
for r in rows:
    by[r['iid']][r['cfg']] = r
cfgs = sorted({r['cfg'] for r in rows if r['cfg'] != 'base:v4r:None'})
full = [i for i, d in by.items() if len(d) == 1 + len(cfgs)]
print(f'{len(full)} instances complete; evaluator/internal agree on all rows: {all(r["agree"] for r in rows)}')

def gm(xs):
    return math.exp(sum(map(math.log, xs)) / len(xs)) if xs else float('nan')

for kind, metric, refk, ok in (('mk', 'ms', 't_fast', lambda r: r['cost'] <= r['B']),
                               ('cost', 'cost', 'cost_floor', lambda r: r['ms'] <= r['D'])):
    print(f'\n== {kind}: {metric}/{refk} (only rows satisfying the hard constraint), vs DCR-v4R single run ==')
    print(f'{"config":22} {"ok":>5} {"geomean":>8} {"median":>8} {"tight":>7} {"moder":>7} {"relax":>7} {"<v4R":>5} {"=v4R":>5} {">v4R":>5} {"probes":>6} {"rt_s":>6}')
    for cfg in ['base:v4r:None'] + [c for c in cfgs if c.startswith(kind + ':')]:
        rs = [by[i][cfg] for i in full]
        good = [r for r in rs if ok(r)]
        ratios = [r[metric] / r[refk] for r in good]
        q = {qq: gm([r[metric] / r[refk] for r in good if r['qos'] == qq]) for qq in ('tight', 'moderate', 'relaxed')}
        w = t = l = 0
        for i in full:
            r, b = by[i][cfg], by[i]['base:v4r:None']
            if not ok(r):
                l += 1; continue
            if not ok(b):
                w += 1; continue
            w += r[metric] < b[metric]; t += r[metric] == b[metric]; l += r[metric] > b[metric]
        print(f'{cfg:22} {len(good):>5} {gm(ratios):8.4f} {statistics.median(ratios) if ratios else float("nan"):8.4f} '
              f'{q["tight"]:7.3f} {q["moderate"]:7.3f} {q["relaxed"]:7.3f} {w:>5} {t:>5} {l:>5} '
              f'{statistics.median(r["probes"] for r in rs):>6} {statistics.median(r["rt"] for r in rs):6.2f}')
