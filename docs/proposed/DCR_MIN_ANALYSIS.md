# DCR-Min: analysis

Companion to `docs/proposed/DCR_MIN.md`. Every number here is printed by
`docs/proposed/dcr_min_analysis/analyse.py` (output: `analysis.txt`, sections A–D).
Data: the 160-instance dev study (A), probe traces and 40-point oracle sweeps on the 70 dev instances with
60–200 tasks (B), and greedy baselines (C, D). The raw JSONL/CSV inputs are not committed.
They can be regenerated with the scripts in `dcr_min_analysis/` and `tools/minimise.py`.

## 1. Verdict

* **Min makespan under budget: DCR-Min is strong.** It is budget-safe by construction. It cuts makespan by
  about 32% against one DCR-v4R run, and it beats the classic budget-constrained heuristics LOSS1 and GAIN by
  3–4× on geo-mean (156/160 and 70/70 instances). Twelve probes are enough.
* **Min cost under deadline: DCR-Min works, but it is not clearly better than a simple greedy.** A deadline-LOSS
  greedy, with the evaluator in its loop, ties DCR-Min on the median instance (DCR-Min/LOSS = 0.99).
  It wins on tight instances and on half of the 400-task ones. The cause is structural (§3): DCR spends whatever
  budget it is given, so the only lever is the budget knob, and the cost search can only be as good as that
  one-dimensional knob.
* **Best configuration found:** DCR-Min-cost followed by a LOSS polish from its plan. It reaches 0.845 vs 0.882
  cost/floor, improves 87/94 instances, and beats stand-alone LOSS on 69/94. It adds about 22% runtime.

## 2. Guarantees

| Property | Status | Why |
|---|---|---|
| Min-makespan plan respects B | **Proved** (given Σ cmin ≤ B) | Every DCR member (v1, the v4 scoring base, and the v2/v3 rescue members) admits a resource only if `spent + c_ir + reserve − cmin_i ≤ B`, and raises an error otherwise. Cost depends on the placement alone, so DCR's internal calendar and the evaluator cannot disagree on it. |
| Min-cost plan meets D | **Empirical** | The search keeps only plans whose *internal* makespan ≤ D. The evaluator agreed with that calendar on 480/480 runs here, and on every stored run, but nothing forces agreement. |
| Never worse than its own probes | Proved | It returns the best constraint-satisfying probe. |
| Optimality | **None** | Only status `optimal_at_cost_lb` would be a proof. It never fired (0/160): the LB_C(D) probe met D on 0/70 traced instances, and LB_C(D) = 0 on 49/70. |
| Lower bounds | Valid but weak | Final DCR-Min / LB is about 3.1–4.1 for makespan and 5.2–7.0 for cost (geo-mean, summary §4). They certify nothing useful. |
| Runtime | ≤ 12 oracle runs | Each oracle run is DCR-v4R: at most 14 step loops, O(n²m + em + nm log m). Measured scaling is about n^1.4, the same exponent as one DCR-v4R run (A4), at 55–80× the constant. |

## 3. How the oracle responds to its knob (B3, A1)

* **Budget is spent, not saved.** At a probed budget b, DCR's cost/b has median 0.996 (10th percentile 0.76).
  On the 160 instances, one DCR-v4R run uses a median 97% of B but only 55% of D. So DCR is effectively
  *makespan-greedy within budget*. This explains both results:
  * It is a natural engine for min-makespan: give it the true B and a deadline target to push.
  * For min-cost, the search can only lower cost by lowering the budget it hands DCR. A cheaper plan that needs
    a non-greedy placement at some budget is invisible to it.
* **The deadline knob is a target, not a constraint.** The achieved makespan divided by the probed deadline
  ranges from 0.07 to 86 (median 0.95). On 68/70 instances, a *looser* probed deadline gave a *shorter* makespan
  somewhere on the sweep, so makespan is not monotone in the knob. Descent (shrinking from the incumbent)
  handles this better than bisection, which is why tuning chose it.
* **Feasibility in the budget is nearly an interval, but not exactly.** On the 40-point sweep, no instance met D
  at one budget and missed it at the next larger one (0/70). The one cost loss (B5) shows it is not exact at fine
  resolution:
  * b = 2.56e12 (the instance budget) meets D, at makespan/D = 1.0000, with v4's plan rejected and the v3 rescue
    portfolio's plan chosen.
  * b = 2.60e12 misses D (1.90×).
  * b = 2.66e12 meets D again.

  Bisection stepped on 2.60e12, moved its lower end up, and never returned. Only 3/41 sweep budgets meet D on
  that instance. The cheap feasible point is a knife edge produced by the rescue portfolio.

## 4. Convergence and probe budget (B1, B2)

| Probes k | 1 | 2 | 3 | 4 | 6 | 8 | 10 | **12** | 16 | 24 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| makespan / best-of-sweep | 2.47 | 1.43 | 1.17 | 1.08 | 1.02 | 1.005 | 0.997 | **0.990** | 0.988 | 0.987 |
| cost / best-of-sweep | – | 4.33 | 2.42 | 1.53 | 1.06 | 0.960 | 0.936 | **0.930** | 0.929 | 0.929 |

* Twelve probes sit on the plateau: doubling to 24 gains 0.3% (makespan) and 0.1% (cost). Eight probes would
  lose about 1.5% / 3% and save a third of the runtime.
* The adaptive 12-probe search beats a dense 40-point log sweep of the same knob: it is better, equal or worse on
  43/15/12 instances for makespan and 57/9/4 for cost. Placing probes next to the frontier matters more than
  covering the range.
* The winning probe is usually late (indices 8–11 for most instances), so the search keeps improving until the cap.
* **Wasted start probes:**
  * Cost probe 0 (budget LB_C(D)) never met D (0/70). LB_C(D) is 0 on 49/70 instances because tasks can run free
    on IoT one at a time, so the bound ignores contention.
  * The makespan 2× slack start probe has no effect when removed (geo-mean 0.997, better on 19, worse on 12).
  * Both probes could be reallocated to the search.

## 5. Where the gains are (A2, summary §3)

* **QoS dominates.**
  * Relaxed instances gain most: cost falls to 0.06× one DCR-v4R run and makespan to 0.58×.
  * Tight instances gain least: 0.95× cost and 0.91× makespan.
  * A tight instance leaves little room, and a single DCR run already lands near the frontier there.
* **Size and family matter little.** Gains are flat across 60–1000 tasks: makespan 0.64–0.77×, cost 0.23–0.30×
  vs DCR-v4R. Across families, montage gains most on makespan (0.59×). sipht is the only family above the
  calibrated cost floor (1.01×).
* **The tuning subset is not special.** Untouched vs tuning instances: makespan/t_fast 1.507 vs 1.402, and
  cost/floor 0.834 vs 0.907. The gap goes both ways, so there is no sign of overfitting.

## 6. Comparison with classic greedy minimisers (C, D)

Sakellariou et al. (2007) give the standard budget-constrained baselines, LOSS and GAIN. For cost under a
deadline, the analysis adds the matching "deadline-LOSS" (start from HEFT-IFC, downgrade while the evaluated
makespan ≤ D).

| Problem | Method | Instances | geo-mean ratio (lower = better) | DCR-Min better / worse |
|---|---|---:|---:|---:|
| makespan s.t. B | DCR-Min | 160 | **1.483** (/t_fast) | – |
| | LOSS1 (from HEFT) | 160 | 4.557 | 156 / 2 |
| | GAIN (from cheapest) | 70 | 5.398 (DCR-Min 1.424) | 70 / 0 |
| cost s.t. D | DCR-Min | 94 | 0.882 (/floor) | – |
| | deadline-LOSS | 94 | 0.957 | 54 / 40 |
| | **DCR-Min + LOSS polish** | 94 | **0.845** | (beats LOSS 69 / 24) |

* **Makespan.** The classic methods rank moves by execution time alone, so they push work to free IoT nodes and
  then lose the time on the network. DCR plans on the communication-aware calendar and avoids that.
* **Cost:**
  * The median DCR-Min/LOSS ratio is 0.99, with a wide spread (0.30–1.41).
  * DCR-Min wins clearly on relaxed instances (23/8) and loses on tight ones (14/18).
  * At 400 tasks it is 11/13.
  * LOSS also calls the evaluator in its loop (about 400 evaluations per instance), which DCR-Min never does.
    With today's evaluator it is as fast as or faster than DCR-Min (median 1.3 s vs 5.3 s at ≤ 200 tasks; both
    about 25 s at 400 tasks).
* **Polish.** Running the same LOSS loop from DCR-Min's plan, rather than from HEFT, improves 87/94 instances.
  The median gain is 1.5% and the best is 40%. It is largest on moderate instances (0.872 → 0.795). Median
  polish time is 1.7 s on top of 7.8 s for DCR-Min.

## 7. Failure modes found

1. **Knife-edge feasible budgets (cost).** The cybershake-600 tight instance (§3). The cost search returned 13%
   more than a single DCR-v4R run at the instance budget.
2. **Start probes that cannot succeed** (§4). They cost 1 of 12 probes on every instance.
3. **Dependence on calendar/evaluator agreement for the deadline** (§2). It held on every instance, but a
   future evaluator change could break min-cost silently. A final evaluator check would be cheap (one
   evaluation) and would remove the risk.
4. **Ties on tight instances.** On three instances, all tight (genome-1000, montage-200, sipht-60), DCR-Min only
   matches one DCR-v4R run for makespan. That is expected when the budget allows no faster plan, but there is
   no certificate to say so.

## 8. Recommended changes (none applied yet)

| Change | Expected effect | Evidence |
|---|---|---|
| Add LOSS polish after DCR-Min-cost | −4.2% cost geo-mean, +~22% runtime | §6, D |
| Replace the LB_C(D) start probe with a probe at the polished/HEFT plan's cost, or drop it | One more useful probe | B2 |
| Drop the 2× slack start probe for makespan | Neutral quality, one more probe | B4 |
| End min-cost with one descent step below the incumbent, and try the incumbent ± a small band | Guards against knife-edge budgets | B5 |
| Add one final evaluator check to both wrappers (fall back to the next-best probe if it fails) | Makes deadline compliance a guarantee, not an observation | §2 |
| `max_probes` 8 when speed matters | −33% runtime for +1.5% / +3% | B1 |

## 9. Threats to validity

* **Dev split only.** The defaults were tuned on 35 of these 160 instances (the effect is checked in §5).
  The expansion and unseen sets are not run.
* **References are calibration schedules, not optima.** `t_fast` and `cost_floor` come from the hidden QoS
  calibration. DCR-Min goes below `cost_floor` on 141/160 instances, so ratios measure relative quality only.
  An exact model (MILP/CP) on the 60-task instances would give true gaps.
* **Baselines are simple but standard.** The LOSS/GAIN variants use a fixed task order and execution-time
  weights. A communication-aware LOSS (weights from evaluated makespan, as in LOSS2) is a stronger rival for the
  cost problem and is not yet tried.
* **Runtime figures come from a 2-core cloud VM running 2 processes.** Ratios between methods are more reliable
  than absolute seconds.
