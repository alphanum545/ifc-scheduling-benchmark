# DCR-v1 Admission component ablations (paper 1), predeclared 2026-10-24

This protocol is fixed before any ablation result exists. The code is in `algorithms/dcr_ablations/`, and the variants are registered in `algorithms.toml` with `role = "ablation"` and `enabled = false`.

## Question

Which components of DCR-v1 Admission produce its joint-feasibility gain? The pre-registered A/B/C ablation in the DCR-v1 spec already isolated the child-arrival correction:

| Spec variant | Algorithm | What it shows |
|---|---|---|
| A | DCR-v0 optimized | capacity-only reserve |
| B | DCR-v1 Admission | the proposed method |
| C | DCR-v1 full ranking | corrected reserve also used for ranking |

These ablations isolate the remaining core components.

## Variants

Each variant changes exactly one component of DCR-v1 Admission. Everything else is the identical step loop.

| ID | Component removed or replaced | Definition |
|---|---|---|
| `dcr-abl-control` | none | Must reproduce DCR-v1 Admission decisions exactly. This verifies the harness. |
| `dcr-abl-no-reserve` | priced reserve admission (R) | Admission and budget loss use only the raw cheapest-remaining reserve, B − spent − Σ cmin, which is the classic prior-art reserve. There is no priced bound and no child-arrival sweep. Time screens are unchanged. |
| `dcr-abl-zero-prices` | dual prices (P) | The same pool and child-arrival sweep, but all three price vectors are zero. The bound becomes the sum of the cheapest timely options, with no capacity pricing. |
| `dcr-abl-time-rank` | minimax ranking (M) | Admitted candidates are ranked by time loss only. |
| `dcr-abl-budget-rank` | minimax ranking (M) | Ranked by budget loss only. |
| `dcr-abl-weighted-rank` | minimax ranking (M) | Ranked by 0.5·time loss + 0.5·budget loss. The weight 0.5 is the conventional default of the weighted comparators; it is not fitted. |

Ties after the replaced primary key are broken by (finish, cost, resource), as in v1.

**Always kept**, because these are safety or time mechanics rather than the contribution:
- the raw budget invariant (so every variant stays budget-safe);
- the latest-finish, domain and capacity time screens;
- the task priority;
- the budget-safe fallback.

## Runs

- Instance sets: `dev` (160) and `expansion` (1,890). The unseen and holdout sets are never used for ablations.
- Repetitions: 1. Ablation runtimes are not reported, so the runs use all cores per machine.
- Primary outcome: joint feasibility, with every variant compared with control by the exact McNemar test (Holm-corrected over the five variants).
- Secondary outcomes: deadline met, budget met, and, where both are feasible, makespan and cost ratios against control.
- All results are reported, whatever they show. The DCR-v1 Admission code and parameters are not changed in response.

## Faithfulness checks (`tests/test_dcr_ablations.py`)

- **Control:** on 150 random synthetic instances, control reproduces DCR-v1 Admission's task order, mapping, planned-assignment hash, makespan, cost and fallback statistics exactly.
- **Variants:** every variant returns a complete mapping, never exceeds the budget when Σ cmin ≤ B, and differs from control on at least one instance.
- **Benchmark run:** the control's schedule on every dev and expansion instance must equal DCR-v1 Admission's stored schedule.
