# Paper-1 supporting experiments: protocols fixed before running (2026-10-24)

The headline algorithm is frozen: **DCR-v1 Admission**, with DCR-v3 Rescue as the extension. Neither is changed in response to any result below, and every outcome is reported.

## 1. Tuned comparators

- **Variants** (`algorithms/tuning`, `role = "tuning"`): BDC ω, BDDC ω and BDHEFT α ∈ {0.1, 0.3, 0.7, 0.9}. The registered comparators already cover 0.5. Each variant overrides only the published weight; the audited comparator code is unchanged.
- **Runs:** dev (160) and expansion (1,890), one repetition.
- **Analysis A, honest tuning.** For each comparator, choose the weight with the highest dev joint feasibility (ties go to the weight closest to 0.5). Report that weight's expansion result against DCR-v1 Admission, using an exact McNemar test.
- **Analysis B, oracle bound.** Report the best weight chosen on expansion itself, and the per-instance best of all five weights (virtual best over weights). Both are upper bounds that favour the comparator.

## 2. Deadline × budget tightness grid (`ifc-grid-v1`)

- **Instances:** the 159 development base realizations, each with 25 joint QoS cells. The deadline fraction is α ∈ {1/100, 1/20, 1/4, 1/2, 3/4} and the budget fraction is β ∈ {1/10, 3/10, 1/2, 7/10, 9/10}. That makes 3,975 instances, with the v1 profiles as three of the cells.
- **Construction:** built with the unchanged v1 calibration. Rebuilt bases must equal the frozen dev bases byte for byte. Holdout bases are excluded.
- **Freezing:** frozen by "Freeze grid set" before any scheduler runs, then regenerated and verified by "Prepare data".
- **Run:** all 12 enabled algorithms, once.
- **Outcome:** joint-feasibility rate per cell (heatmap), and the DCR-v1 Admission minus BDC difference per cell.

## 3. Robustness to noise, and IoT/fog/cloud placement (`tools/robust.py`)

- **Decisions:** each enabled algorithm's decision on each dev instance, computed once on the nominal instance.
- **Perturbations:** the decision is kept fixed and re-evaluated by the pinned evaluator under K = 10 seeded perturbations at each noise level d ∈ {0.1, 0.2, 0.3}.
  - Every execution time is multiplied by an independent factor U(1−d, 1+d), with compute cost and energy recomputed from it.
  - Every network-segment bandwidth is multiplied by an independent factor U(1−d, 1+d).
  - The perturbations are seeded by (instance, d, k) only, so all algorithms see identical perturbed instances.
- **Outcomes:**
  - the share of nominally jointly feasible schedules that stay feasible, averaged over draws;
  - the overall perturbed joint-feasibility rate;
  - the median makespan/D under noise.
- **Placement (nominal schedules):** per tier, the share of tasks, of busy time and of compute cost.

## 4. Exact feasibility of small instances (`tools/exact.py`)

- **Instances:** every 60-task dev and expansion instance.
- **Model:** OR-tools CP-SAT with the evaluator's exact semantics: serial resources, transfer times by tier pair, zero transfer on the same resource, the deadline and the budget.
- **Limits:** 120 s and 4 workers per instance, with a fixed random seed.
- **Statuses:**
  - FEASIBLE: the found schedule is rebuilt by the pinned evaluator and must be jointly feasible;
  - INFEASIBLE: proved;
  - UNKNOWN: the time limit was reached.
- **Use:** the share of DCR's failures that are proved infeasible, and the share of instances provably feasible that DCR misses.

## 5. Unseen-workflow test (`ifc-unseen-v1`)

All 12 enabled algorithms are run once on the frozen 2,241-instance set, and the results are reported as they are.
