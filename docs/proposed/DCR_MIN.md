# DCR-Min: DCR for the minimisation variants

The benchmark asks a satisficing question: does a schedule meet the deadline D **and** the
budget B? DCR (all versions) is built for that question. This note covers the two
single-objective variants:

| Variant | Objective | Constraint | Ignored |
|---|---|---|---|
| `dcr-min-makespan` | minimise makespan | compute cost <= B | D |
| `dcr-min-cost` | minimise compute cost | makespan <= D | B |

Analysis (guarantees, convergence, failure modes, greedy baselines): `docs/proposed/DCR_MIN_ANALYSIS.md`.

Code: `algorithms/dcr_min/`. Study driver: `tools/minimise.py`. Results:
`results/minimise/summary.md` (the per-run CSVs are not committed; regenerate them with
`tools/minimise.py run`, about 3.5 h on 2 cores, then `tools/minimise.py report`). Tests: `tests/test_dcr_min.py`.

## Why DCR alone is not a minimiser

* **Both D and B are hard-wired.** The priced reserve, latest-finish bounds `b_i = D - h_i`,
  checkpoints `θ = D·k/4` and price scale `H = 2D²` all depend on D; the budget invariant
  depends on B. There is no "free" objective.
* **The ranking is objective-blind.** The minimax slack-loss rule picks whatever keeps
  both constraints satisfiable; once that is true, it does not push makespan or cost further.
  It stops at "feasible".
* **Its fallback is earliest-finish within budget.** That is a makespan-leaning heuristic, not a
  cost minimiser.
* **It is not monotone in D or B.** Meeting D does not imply meeting a larger D, so a naive
  bisection over the constraint is not guaranteed to be valid.

## Design: DCR as an unchanged oracle inside a bounded search

No DCR rule or parameter is changed. The wrapper calls the oracle (DCR-v4R by default) with
a *probed* deadline (min-makespan) or budget (min-cost), and reads DCR's own insertion-calendar
plan back (`internal_makespan_us`, `internal_compute_cost_ncu`) — the same self-check DCR-v4R
uses. It keeps the best plan that satisfies the real constraint.

* **Min-makespan.** Because DCR always keeps its raw cheapest-remaining budget invariant, every
  probe respects B whenever `Σ cmin ≤ B`. Start probes: target `LB_T`, then `2 × best`. Then
  `descent`: target `best·(1-δ)`, δ starts at 1/8, doubles on improvement (cap 1/4), halves on
  failure, stops below 1/256.
* **Min-cost.** Probe budget `LB_C(D)` first (if it meets D, it is provably optimal), then
  `Σ cmax`. Then `bisect` on the budget between `LB_C(D)` and the incumbent cost.
  Only plans meeting D count; if none does, the fastest plan is returned and flagged.
* At most 12 oracle runs per instance.

Lower bounds (valid for any schedule, communication ignored):

    LB_T    = max( max_i (a_i + pmin_i + h_i),  ceil(Σ pmin_i / m) )
    LB_C(D) = Σ_i min{ c_ir : a_i + p_ir + h_i ≤ D }   (None ⇒ D is certified infeasible)

The plain `Σ cmin` is 0 on every dev instance (IoT execution is free), which is why the
deadline-aware `LB_C(D)` is needed.

## Tuning

Grid: oracle ∈ {DCR-v1 Admission, DCR-v4, DCR-v4R} × strategy ∈ {bisect, descent, hybrid},
on 35 dev instances (every second instance with ≤ 200 tasks). Script, per-config report
(`grid.txt`) and the instance list (`tuning_ids.txt`): `docs/proposed/dcr_min_tuning/`. Geo-mean ratios (lower is better):

| Config | makespan / t_fast | cost / cost_floor |
|---|---:|---:|
| single DCR-v4R run | 1.928 | 2.666 |
| v4R + descent | **1.402** | 0.932 |
| v4R + bisect | 1.408 | **0.907** |
| v4R + hybrid | 1.411 | 0.921 |
| v4 oracle (best strategy) | ≈1.53 | ≈1.09 |
| v1 Admission oracle (best strategy) | ≈1.63 | ≈1.15 |

Chosen: DCR-v4R oracle, descent for makespan, bisect for cost. The stronger the oracle,
the better the search, so DCR-v4R's rescue portfolio is worth its cost here.

## Results (160 dev instances)

See `results/minimise/summary.md` for full tables, including the stored comparators
(BDC, BDHEFT, BDSD, DBCS, BDDC, HEFT-IFC, PEFT-IFC, DCR-v1 Admission) and the split between
tuning and untouched instances.

All 480 schedules (160 × {DCR-v4R, DCR-Min makespan, DCR-Min cost}) were rebuilt and re-checked by
the pinned Dataset evaluator; all agree with DCR's internal plan. Every min-makespan plan respects B
and every min-cost plan meets D (160/160 each).

| Objective (geo-mean, lower is better) | DCR-Min | one DCR-v4R run | DCR-Min better / tie / worse vs DCR-v4R |
|---|---:|---:|---:|
| makespan / t_fast, cost ≤ B | **1.483** | 2.176 | 157 / 3 / 0 |
| cost / cost_floor, makespan ≤ D | **0.850** | 3.280 | 158 / 1 / 1 |

Out of sample (125 untouched instances): makespan 1.507 vs 2.251; cost 0.834 vs 3.478 — the same
picture as the 35 tuning instances (1.402 vs 1.928; 0.907 vs 2.666).

By QoS, the gain is largest when the constraints are loose (relaxed cost: 0.80 vs 12.9) and smallest
when tight (tight makespan: 1.07 vs 1.18), as expected: a tight instance leaves little room to move.

Against the stored comparators (joint-problem runs at the instance D and B), DCR-Min is better on at
least 148/160 instances for makespan and 160/160 for cost. DCR-v1 Admission is the closest on makespan
(12 instances where it is faster).

## Caveats

* **Dev split, partly in-sample.** The 35 tuning instances are in-sample; section 4 of the summary
  reports them separately. The expansion and unseen sets have not been run.
* **Best found, not optimal.** The certified bounds are weak (DCR-Min is 3–7× above them on
  geo-mean), so they do not show closeness to optimal. Only `optimal_at_cost_lb` is a proof.
* **Comparators solve a different problem.** The stored rows were run for the joint problem at
  the instance D and B; they are a reference, not tuned minimisers. A fair rival is a
  minimisation baseline (e.g. a MILP/CP model on small instances, or a budget-sweep of BDC).
* **`cost_floor` is a calibration reference, not a lower bound.** DCR-Min going below it is
  expected and only means the calibration's floor heuristic is beatable.
* **Runtime.** About 12 oracle runs, so roughly 55–80× one DCR-v4R run in the median; up to
  several minutes on the largest instances on a 2-core VM.
