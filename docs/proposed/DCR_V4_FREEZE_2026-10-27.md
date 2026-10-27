# DCR-v4 freeze and unseen-set confirmation protocol (2026-10-27, written before any unseen result)

## The method being frozen

**DCR-v4** (`dcr-v4-quality`, `algorithms/dcr_ifc_v4/`, version `dcr_ifc_v4_quality_freeze_20261027`):
- **Admission (unchanged from DCR-v1 Admission):** a placement is admitted only if the deadline- and capacity-aware
  priced lower bound on the remaining cost, with the exact child-arrival correction, still fits the budget. The raw
  cheapest-remaining invariant keeps the schedule budget-safe.
- **Ranking (new):** admitted candidates are ranked by BDC's weighted Quality with ω = 1/2:
  - TQ = (b_i − FT − FT_min)/b_i;
  - CQ = (RB − TC − TC_min)/RB, with RB = B − spent;
  - the highest (TQ + CQ)/2 wins; ties go by (finish, cost, resource).
- **Everything else is DCR-v1 Admission:** task priority, time screens, fallback and price epochs.

**Identity:** DCR-v4 reuses the step loop of the measured ablation variant `dcr-abl-bdc-score`, so its decisions are
identical by construction. This is checked two ways:
- `tests/test_dcr_v4.py`: equal on 150 random instances, and budget-safe;
- a local run: 160/160 dev schedules equal the stored CI schedules of `dcr-abl-bdc-score`.

No parameter is tuned. ω = 1/2 is the preregistered comparator default (`BDDC_BDC_2021.md`).

## How it was chosen (full disclosure)

Five rankings of DCR-admitted candidates have been evaluated, all on **dev and expansion only**:

| Ranking | Expansion joint |
|---|---:|
| minimax slack loss (DCR-v1) | 86.2% |
| time only | 52.1% |
| budget only | 50.8% |
| 0.5/0.5 weighted slack loss | 87.8% |
| BDC Quality (ω = 1/2) | **91.6%** |

The table covers the ranking variants. The zero-price and no-reserve variants change other components, not the
ranking.

DCR-v4 is the best of these, so its dev and expansion numbers are **selection-biased** and must not be presented as an
unbiased estimate. The unseen set (`ifc-unseen-v1`, 2,241 instances, 83 DAGs) was **never used** for any ranking
choice. It has been run only with the frozen algorithms (2026-10-24) and BDCWS (2026-10-26). So it is a clean
out-of-sample test for this choice. This corrects the more cautious wording in EVIDENCE_PACK §6c, consequence 3.

## Confirmation protocol (fixed now)

- **Run:** Benchmark, `set = unseen`, `algos = dcr-v4-quality`, 1 repetition, **run once**. It is not rerun, retuned or
  replaced after the result is seen. Dev and expansion runs of `dcr-v4-quality` are also made, for the tables only.
- **Primary outcome:** joint feasibility on unseen, DCR-v4 against DCR-v1 Admission, exact two-sided McNemar test.
- **Secondary outcomes:**
  - DCR-v4 against BDC, BDCWS, BDSD, DBCS and BDHEFT (exact McNemar, Holm over these five);
  - breakdowns by QoS, family and source (new families / new replicates);
  - makespan and cost ratios where both are feasible;
  - paired runtime against BDC on the same CI runners.
- **Decision rule:**
  - *Adopt as headline:* DCR-v4 becomes the paper's headline method if it is **not significantly worse** than DCR-v1
    Admission on unseen. Significantly worse means p < 0.05 with more cases only DCR-v1 solves.
  - *If adopted:* DCR-v1 Admission is reported as the base variant, and the ranking result as the ablation (§6c).
  - *If not adopted:* DCR-v1 Admission stays the headline, and DCR-v4 is reported as an ablation finding that did not
    transfer.
  - Either way, every number is reported.
- **The selection is reported, not hidden.** The paper states that the ranking was chosen among the variants above
  on dev and expansion, and that unseen is the confirmation.

## Consequences if adopted (to do after the confirmation, not before)

1. **Rerun the remaining experiments for DCR-v4:** the tightness grid (`grid`), the robustness noise study and the
   exact CP-SAT comparison. The tuned-comparator analysis does not change.
2. **Decide on DCR-v3 Rescue,** which is built on DCR-v1's ranking:
   - keep it as an extension of v1;
   - rebuild its champion on v4, which needs a new freeze and test;
   - or drop it.
3. **Update the method section and the novelty claim.** The contribution is the deadline-aware reserve admission, and
   the ranking is a conventional weighted quality.
