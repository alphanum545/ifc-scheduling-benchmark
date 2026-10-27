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

## Addendum, 2026-10-27: scoring ablation (predeclared before any result)

Agreed in the evidence pack (§7b, status table). It was deferred until the GitHub runners were free.

**Question.** §6b showed that the deadline-aware reserve matters: no-reserve is −2.6 pp overall and −7.5 pp at
tight QoS. §6b did not separate the effect of DCR's *slack-relative* scoring from BDC-style normalization. BDCWS
(added 2026-10-26) is the mirror image: a deadline-blind reserve with deadline-aware scoring. This ablation keeps
DCR's reserve and swaps only the scoring.

**Code.** `algorithms/dcr_ablations_scoring/` is a separate copy of the ablation step loop, so the 2026-10-24
ablation sources, hashes and stored results are unchanged.

| ID | Component replaced | Definition |
|---|---|---|
| `dcr-abl-scoring-control` | none | Must reproduce DCR-v1 Admission decisions exactly |
| `dcr-abl-bdc-score` | minimax slack ranking (M) | Admitted candidates are ranked by BDC's Quality, as implemented in `algorithms/bddc_bdc` with ω = 1/2. TQ = (SDL − FT − FT_min)/SDL, with SDL = the task's latest finish b_i (DCR's counterpart of BDC's level sub-deadline). CQ = (RB − TC − TC_min)/RB, with RB = B − spent (BDC's whole remaining budget; CQ = 0 if RB = 0). The highest (TQ + CQ)/2 wins; ties (finish, cost, resource) |

**Kept unchanged:**
- priced-reserve admission, with the child-arrival correction and the three price vectors;
- the raw budget invariant;
- the time screens;
- the task priority;
- the fallback.

**Runs and analysis.** These are the same as above:
- sets `dev` and `expansion`;
- 1 repetition;
- exact McNemar test against `dcr-abl-scoring-control`, with secondary outcomes as above.

Holm correction now covers six variants. All results will be reported whatever they show, and DCR-v1 Admission is
not changed in response.

**How the result will be read:**
- If `dcr-abl-bdc-score` is significantly worse than control, DCR's slack-relative scoring contributes beyond the
  reserve.
- If it is not significantly different, the gain is attributed to the reserve, and the paper must not claim the
  scoring as a source of gain.

**Faithfulness checks (`tests/test_dcr_ablations_scoring.py`):**
- the control equals DCR-v1 Admission on 150 random instances;
- the variant is complete, budget-safe and differs from the control somewhere;
- in the benchmark run, the control's schedules must equal DCR-v1 Admission's stored schedules on every dev and
  expansion instance.
