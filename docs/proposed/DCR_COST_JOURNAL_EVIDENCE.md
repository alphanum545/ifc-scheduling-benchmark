# DCR-Cost journal evidence

This single GitHub Actions run evaluates the frozen Paper 2 scheduler at
`d4f8468b27f0f0f5b005f82f4ec3c7ea89590a34`. The target is compute cost among schedules
whose makespan meets the deadline. The pinned evaluator rebuilds every new decision and
independently checks it. A valid decision can miss its deadline. Coverage includes those misses.

## Protocol

- Evaluate all 1,890 expansion and 2,241 unseen instances in the frozen manifests. Keep expansion
  and unseen results separate. The earlier 495-case sample belongs to expansion.
- Compare v3 with v1, v2, CMaS, IC-PCP, and ProLiS seeds 0–9. Reuse source-matched, validated
  repository results. Report ProLiS seed coverage, the mean feasible seed cost, and the best feasible
  seed cost. Both aggregates condition on at least one feasible seed.
- For mechanism and runtime comparisons, take one instance per family × task count × QoS cell,
  using the smallest SHA-256 of the instance identifier. This selects 105 expansion and 177 unseen
  cases before evaluation. Run policies serially on the same worker. Recheck any stored v2 fingerprint
  used in this paired sample.
- Evaluate the frozen v3 with pricing alone (skip final deep polish) and polish alone
  (no priced candidates). Give a second v2 search the same scheduling wall time measured for v3
  on that worker. It starts from scratch and then tries finer deadline splits in dyadic order.
  Only complete, feasible incumbents available by the cutoff count. If v2 itself finishes late,
  the control has no incumbent at cutoff; the raw row retains its later result for auditing.
  One in-flight operation can finish late. The raw data includes both the cutoff and elapsed time.
  Timing excludes authoritative evaluation for every method.
- Report feasibility for each algorithm, paired wins/ties/losses and cost ratios when both meet
  the deadline. Ratios use positive comparator costs. Group results by workflow family, size, QoS,
  infrastructure scenario/scale, and unseen source type where available. Overall uncertainty
  intervals resample source DAGs 1,000 times with seed 71023.
- Reuse the verified CP-SAT references on the 270 expansion cases with 60 tasks. Distinguish
  a feasible incumbent from a proven optimum. Compare the new v3 costs and makespans with
  all 495 historic compact rows. A disagreement fails the report.
- Interpret the comparator results under the IFC resource and cost model. ProLiS and IC-PCP required
  substantial adaptations. The evidence supports comparisons with the registered methods.
  It does not measure PACM, WSEFC-GA, a live deployment, or a separate protected pilot holdout.
  See the [baseline audit](../paper_audits/PAPER2_BASELINE_TRIAGE.md).

## Run and output

Opening the `paper2-dcr-cost-evidence` pull request against `paper2-dcr-cost-v3` launches the
campaign once. Later commits to that PR do not relaunch it. After integration on the default
branch, the workflow also supports manual dispatch. It checks the frozen schedule sources,
evaluator pin, and manifests before measurement and uses read-only repository permissions.

The report job publishes **DCR-Cost-journal-evidence** as a GitHub Actions artifact for 90 days.
It contains the run-level CSV with source and schedule hashes, feasibility and runtime tables,
paired comparisons, CP-SAT and historical replay tables, the frozen protocol and file digests.
Individual shard CSVs remain available if a job fails. Re-running failed jobs in the same run
restores complete cases from their checkpoint. A complete, validated matrix is required for
publication of the aggregate report.
