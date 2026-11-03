"""Reproduce every number in docs/proposed/DCR_MIN_ANALYSIS.md.

usage (repo root): python3 docs/proposed/dcr_min_analysis/analyse.py > docs/proposed/dcr_min_analysis/analysis.txt

Inputs: results/minimise/dev-*.csv (tools/minimise.py run) and the JSONL files written next to
this script by trace.py, baselines.py, loss_makespan.py and polish.py.
"""
import collections
import csv
import glob
import json
import math
import statistics as S
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def gm(xs):
    xs = list(xs)
    return float('nan') if not xs else math.exp(sum(math.log(max(x, 1e-12)) for x in xs) / len(xs))


def qs(xs, ks=(0, .1, .25, .5, .75, .9, 1)):
    xs = sorted(xs)
    return [round(xs[int(k * (len(xs) - 1))], 3) for k in ks]


def jl(pattern):
    return [json.loads(x) for p in sorted(HERE.glob(pattern)) for x in p.read_text().splitlines() if x.strip()]


rows = [r for p in sorted(glob.glob(str(ROOT / 'results/minimise/dev-*.csv'))) for r in csv.DictReader(open(p))]
by = collections.defaultdict(dict)
for r in rows:
    by[r['instance_id']][r['algo']] = r
I = lambda r, k: int(r[k])  # noqa: E731
print(f'== A. Full study: {len(by)} instances, {len(rows)} runs ==')

print('\n-- A1. How one DCR-v4R run uses the limits (fraction of D and B), quantiles 0/10/25/50/75/90/100%')
v4 = [d['dcr-v4-rescue'] for d in by.values()]
print(' makespan / D ', qs(I(r, 'makespan_us') / I(r, 'deadline_us') for r in v4))
print(' cost / B     ', qs(I(r, 'compute_cost_ncu') / I(r, 'budget_ncu') for r in v4))
print(' DCR-Min-cost makespan / D   ', qs(I(d['dcr-min-cost'], 'makespan_us') / I(d['dcr-min-cost'], 'deadline_us') for d in by.values()))
print(' DCR-Min-makespan cost / B   ', qs(I(d['dcr-min-makespan'], 'compute_cost_ncu') / I(d['dcr-min-makespan'], 'budget_ncu') for d in by.values()))

print('\n-- A2. Breakdown: geo-mean DCR-Min / one DCR-v4R run (makespan; cost), and DCR-Min / reference')
for key in ('family', 'tasks', 'qos'):
    g = collections.defaultdict(list)
    for d in by.values():
        g[d['dcr-v4-rescue'][key]].append(d)
    print(f' by {key}: n | mk/v4R | mk/t_fast | cost/v4R | cost/floor | median runtime mk, cost (s)')
    for k in sorted(g, key=lambda x: int(x) if key == 'tasks' else x):
        ds = g[k]
        print(f'  {k:>10} {len(ds):3} | {gm(I(d["dcr-min-makespan"], "makespan_us") / I(d["dcr-v4-rescue"], "makespan_us") for d in ds):.3f}'
              f' | {gm(I(d["dcr-min-makespan"], "makespan_us") / I(d["dcr-min-makespan"], "t_fast_us") for d in ds):.3f}'
              f' | {gm(I(d["dcr-min-cost"], "compute_cost_ncu") / I(d["dcr-v4-rescue"], "compute_cost_ncu") for d in ds):.3f}'
              f' | {gm(I(d["dcr-min-cost"], "compute_cost_ncu") / I(d["dcr-min-cost"], "cost_floor_ref_ncu") for d in ds):.3f}'
              f' | {S.median(float(d["dcr-min-makespan"]["runtime_s"]) for d in ds):.1f}, {S.median(float(d["dcr-min-cost"]["runtime_s"]) for d in ds):.1f}')

print('\n-- A3. Instances where DCR-Min is not strictly better than one DCR-v4R run')
for i, d in sorted(by.items()):
    a, b = d['dcr-min-makespan'], d['dcr-v4-rescue']
    if I(a, 'makespan_us') >= I(b, 'makespan_us'):
        print(f'  makespan {i[22:]}: DCR-Min {a["makespan_us"]} vs v4R {b["makespan_us"]}')
    a = d['dcr-min-cost']
    if I(b, 'makespan_us') <= I(b, 'deadline_us') and I(a, 'compute_cost_ncu') >= I(b, 'compute_cost_ncu'):
        print(f'  cost     {i[22:]}: DCR-Min {a["compute_cost_ncu"]} vs v4R {b["compute_cost_ncu"]}')

print('\n-- A4. Runtime scaling (least squares on log runtime vs log tasks)')
for algo in ('dcr-v4-rescue', 'dcr-min-makespan', 'dcr-min-cost'):
    pts = [(math.log(int(d[algo]['tasks'])), math.log(max(1e-3, float(d[algo]['runtime_s'])))) for d in by.values()]
    mx, my = S.mean(p[0] for p in pts), S.mean(p[1] for p in pts)
    print(f'  {algo}: runtime ~ n^{sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts):.2f}')

# ---------------------------------------------------------------- traces
R = jl('trace-[01].jsonl')
print(f'\n== B. Probe traces and 40-point oracle sweeps: {len(R)} instances (60-200 tasks) ==')


def bmk(tr, B, k=99):
    return min(p['makespan_us'] for p in tr[:k] if p['cost_ncu'] <= B)


def bc(tr, D, k=99):
    v = [p['cost_ncu'] for p in tr[:k] if p['makespan_us'] <= D]
    return min(v) if v else None


print('\n-- B1. Convergence: geo-mean of best-after-k-probes / best-of-sweep, and / reference')
for k in (1, 2, 3, 4, 6, 8, 10, 12, 16, 24):
    m = [bmk(r['mk_trace'], r['B'], k) for r in R]
    c = [bc(r['cost_trace'], r['D'], k) for r in R]
    cm = [(x, r) for x, r in zip(c, R) if x is not None]
    print(f'  k={k:2}  makespan: /sweep {gm(x / bmk(r["mk_sweep"], r["B"]) for x, r in zip(m, R)):.3f} /t_fast {gm(x / r["t_fast"] for x, r in zip(m, R)):.3f}'
          f'   cost: meets D {len(cm):2}/{len(R)} /sweep {gm((x + 1) / (bc(r["cost_sweep"], r["D"]) + 1) for x, r in cm):.3f}'
          f' /floor {gm((x + 1) / (r["cost_floor"] + 1) for x, r in cm):.3f}')
m12 = [bmk(r['mk_trace'], r['B'], 12) for r in R]
c12 = [bc(r['cost_trace'], r['D'], 12) for r in R]
ms_, cs_ = [bmk(r['mk_sweep'], r['B']) for r in R], [bc(r['cost_sweep'], r['D']) for r in R]
print(f'  12-probe search vs 40-point sweep: makespan better/equal/worse {sum(a < b for a, b in zip(m12, ms_))}/'
      f'{sum(a == b for a, b in zip(m12, ms_))}/{sum(a > b for a, b in zip(m12, ms_))};'
      f' cost {sum(a < b for a, b in zip(c12, cs_))}/{sum(a == b for a, b in zip(c12, cs_))}/{sum(a > b for a, b in zip(c12, cs_))}')
print(f'  probes actually used with cap 24 (median): makespan {S.median(len(r["mk_trace"]) for r in R)}, cost {S.median(len(r["cost_trace"]) for r in R)}')

print('\n-- B2. Which probe (0-based, within 12) produced the returned plan')
for name, key, f, lim, val, ok in (('makespan', 'mk_trace', bmk, 'B', 'makespan_us', lambda p, r: p['cost_ncu'] <= r['B']),
                                   ('cost', 'cost_trace', bc, 'D', 'cost_ncu', lambda p, r: p['makespan_us'] <= r['D'])):
    idx = collections.Counter(next(j for j, p in enumerate(r[key][:12]) if p[val] == f(r[key], r[lim], 12) and ok(p, r)) for r in R)
    print(f'  {name}: {dict(sorted(idx.items()))}')
print(f'  cost start probe at LB_C(D) met D on {sum(r["cost_trace"][0]["makespan_us"] <= r["D"] for r in R)}/{len(R)};'
      f' LB_C(D) = 0 on {sum(r["lb"]["cost_lb_deadline_ncu"] == 0 for r in R)}/{len(R)}')

print('\n-- B3. Oracle response to the probed knob (sweep points)')
print('  makespan sweep: achieved makespan / probed deadline', qs(p['makespan_us'] / p['deadline_us'] for r in R for p in r['mk_sweep']))
print('  makespan sweep: cost / B                            ', qs(p['cost_ncu'] / r['B'] for r in R for p in r['mk_sweep']))
print('  cost sweep:     cost / probed budget (budget < cost_max/2)',
      qs(p['cost_ncu'] / p['budget_ncu'] for r in R for p in r['cost_sweep'] if 0 < p['budget_ncu'] < r['lb']['cost_max_ncu'] / 2))
up = sum(any(b['makespan_us'] < a['makespan_us'] for a, b in zip(r['mk_sweep'], r['mk_sweep'][1:])) for r in R)
flip = sum(any(a['makespan_us'] <= a['deadline_us'] and b['makespan_us'] > b['deadline_us'] for a, b in zip(r['mk_sweep'], r['mk_sweep'][1:])) for r in R)
cflip = sum(any(a['makespan_us'] <= r['D'] < b['makespan_us'] for a, b in zip(r['cost_sweep'], r['cost_sweep'][1:])) for r in R)
print(f'  instances where a looser probed deadline gave a shorter makespan: {up}/{len(R)};'
      f' where a probed deadline was met and the next looser one missed: {flip}/{len(R)}')
print(f'  instances where D was met at a budget and missed at the next larger one: {cflip}/{len(R)}')

print('\n-- B4. Ablations')
a = [r['abl_mk_noslack'] / x for r, x in zip(R, m12)]
print(f'  makespan without the 2x slack start probe / default: geo-mean {gm(a):.4f}, worse on {sum(x > 1 for x in a)}, better on {sum(x < 1 for x in a)}')
w = [((min(x, r['abl_cost_warmB']['cost_ncu']) if r['abl_cost_warmB']['makespan_us'] <= r['D'] else x) + 1) / (x + 1) for r, x in zip(R, c12)]
print(f'  cost with the instance budget B as an extra probe / default: geo-mean {gm(w):.4f}, improves on {sum(x < 1 for x in w)}')

L = jl('trace-loss-case.jsonl')
if L:
    r = L[0]
    print(f'\n-- B5. The one cost loss vs one DCR-v4R run: {r["iid"][22:]} (D={r["D"]}, B={r["B"]})')
    for p in r['cost_trace']:
        print(f'   probe budget {p["budget_ncu"]:.4e}: makespan/D {p["makespan_us"] / r["D"]:.3f}, cost {p["cost_ncu"]:.4e}')
    print(f'   at the instance budget B: makespan/D {r["abl_cost_warmB"]["makespan_us"] / r["D"]:.4f}, cost {r["abl_cost_warmB"]["cost_ncu"]:.4e}')
    print(f'   sweep: {sum(p["makespan_us"] <= r["D"] for p in r["cost_sweep"])}/{len(r["cost_sweep"])} budgets meet D,'
          f' cheapest {bc(r["cost_sweep"], r["D"]):.4e}')

# ---------------------------------------------------------------- baselines
print('\n== C. Classic greedy baselines (Sakellariou et al., 2007) ==')
LM = {x['iid']: x for x in jl('loss_mk-*.jsonl')}
res = [(I(by[i]['dcr-min-makespan'], 'makespan_us'), x['makespan_us'], int(by[i]['dcr-min-makespan']['t_fast_us']), x) for i, x in LM.items()]
assert all(x['cost_ncu'] <= x['B'] for *_, x in res)
print(f'\n-- C1. Min makespan s.t. B, LOSS1 from HEFT-IFC (all {len(res)} instances, all within budget)')
print(f'  makespan/t_fast: DCR-Min {gm(a / t for a, b, t, _ in res):.3f}, LOSS1 {gm(b / t for a, b, t, _ in res):.3f};'
      f' DCR-Min better/tie/worse {sum(a < b for a, b, *_ in res)}/{sum(a == b for a, b, *_ in res)}/{sum(a > b for a, b, *_ in res)}')
print(f'  DCR-Min / LOSS1 quantiles {qs(a / b for a, b, *_ in res)}; LOSS1 runtime median {S.median(x["runtime_s"] for *_, x in res):.2f}s')
BL = {x['iid']: x for x in jl('baselines-*.jsonl')}
g = [(I(by[i]['dcr-min-makespan'], 'makespan_us'), x['gain']['makespan_us'], int(by[i]['dcr-min-makespan']['t_fast_us'])) for i, x in BL.items() if 'gain' in x and x['tasks'] <= 200]
print(f'\n-- C2. Min makespan s.t. B, GAIN from the cheapest assignment ({len(g)} instances <= 200 tasks)')
print(f'  makespan/t_fast: DCR-Min {gm(a / t for a, b, t in g):.3f}, GAIN {gm(b / t for a, b, t in g):.3f}; DCR-Min better on {sum(a < b for a, b, _ in g)}')
c = [(I(by[i]['dcr-min-cost'], 'compute_cost_ncu'), x['loss']['cost_ncu'], int(by[i]['dcr-min-cost']['cost_floor_ref_ncu']), x) for i, x in BL.items()]
assert not any(x['loss']['start_misses_D'] for *_, x in c)
print(f'\n-- C3. Min cost s.t. D, deadline-LOSS from HEFT-IFC with the evaluator in the loop ({len(c)} instances <= 400 tasks; HEFT start meets D on all)')
for name, sub in (('all', c), ('<=200', [z for z in c if z[3]['tasks'] <= 200]), ('400', [z for z in c if z[3]['tasks'] == 400])):
    print(f'  {name:>5} n={len(sub)}: cost/floor DCR-Min {gm(a / f for a, b, f, _ in sub):.4f}, LOSS {gm(b / f for a, b, f, _ in sub):.4f};'
          f' DCR-Min better/worse {sum(a < b for a, b, *_ in sub)}/{sum(a > b for a, b, *_ in sub)}')
for q in ('tight', 'moderate', 'relaxed'):
    sub = [z for z in c if z[3]['qos'] == q]
    print(f'  {q:>8} n={len(sub)}: DCR-Min {gm(a / f for a, b, f, _ in sub):.4f}, LOSS {gm(b / f for a, b, f, _ in sub):.4f}, better/worse {sum(a < b for a, b, *_ in sub)}/{sum(a > b for a, b, *_ in sub)}')
print(f'  DCR-Min / LOSS quantiles {qs(a / b for a, b, *_ in c)}; LOSS runtime median {S.median(x["loss"]["runtime_s"] for *_, x in c):.2f}s'
      f' (<=200: {S.median(x["loss"]["runtime_s"] for *_, x in c if x["tasks"] <= 200):.2f}s, 400: {S.median(x["loss"]["runtime_s"] for *_, x in c if x["tasks"] == 400):.1f}s)')
print(f'  DCR-Min-cost runtime median on the same instances: <=200 {S.median(float(by[i]["dcr-min-cost"]["runtime_s"]) for i in BL if BL[i]["tasks"] <= 200):.2f}s,'
      f' 400 {S.median(float(by[i]["dcr-min-cost"]["runtime_s"]) for i in BL if BL[i]["tasks"] == 400):.1f}s')
print(f'  overall makespan DCR-Min / one DCR-v4R run (geo-mean, 160): {gm(I(d["dcr-min-makespan"], "makespan_us") / I(d["dcr-v4-rescue"], "makespan_us") for d in by.values()):.3f}')

P = {x['iid']: x for x in jl('polish-*.jsonl')}
assert all(x['polished_ms'] <= x['D'] for x in P.values())
assert all(x['dcr_cost'] == I(by[i]['dcr-min-cost'], 'compute_cost_ncu') for i, x in P.items())
pr = [(x['dcr_cost'], x['polished_cost'], BL[i]['loss']['cost_ncu'], int(by[i]['dcr-min-cost']['cost_floor_ref_ncu']), x) for i, x in P.items()]
print(f'\n-- D. DCR-Min-cost + LOSS polish from its plan ({len(pr)} instances <= 400 tasks; every polished plan meets D)')
for name, sub in (('all', pr), ('<=200', [z for z in pr if z[4]['tasks'] <= 200]), ('400', [z for z in pr if z[4]['tasks'] == 400])):
    print(f'  {name:>5} n={len(sub)}: cost/floor DCR-Min {gm(a / f for a, b, l, f, _ in sub):.4f}, +polish {gm(b / f for a, b, l, f, _ in sub):.4f},'
          f' LOSS {gm(l / f for a, b, l, f, _ in sub):.4f}; polish improves {sum(b < a for a, b, *_ in sub)};'
          f' polished vs LOSS better/worse {sum(b < l for a, b, l, *_ in sub)}/{sum(b > l for a, b, l, *_ in sub)}')
for q in ('tight', 'moderate', 'relaxed'):
    sub = [z for z in pr if z[4]['qos'] == q]
    print(f'  {q:>8} n={len(sub)}: DCR-Min {gm(a / f for a, b, l, f, _ in sub):.4f}, +polish {gm(b / f for a, b, l, f, _ in sub):.4f}, LOSS {gm(l / f for a, b, l, f, _ in sub):.4f}')
print(f'  polished/DCR-Min quantiles {qs(b / a for a, b, *_ in pr)}; polish time median {S.median(x["t_polish_s"] for *_, x in pr):.2f}s'
      f' vs DCR-Min {S.median(x["t_dcr_s"] for *_, x in pr):.2f}s')
