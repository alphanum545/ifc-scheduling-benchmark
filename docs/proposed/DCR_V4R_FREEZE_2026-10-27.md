# DCR-v4R freeze (2026-10-27, written before its CI runs)

## Definition

**DCR-v4R** (`dcr-v4-rescue`, `algorithms/dcr_ifc_v4_rescue/`, version
`dcr_ifc_v4_rescue_freeze_20261027_impl1`) is the rescue extension of the headline method DCR-v4 (§6d):

1. Run DCR-v4. If its own plan meets the deadline and the budget (the existing v3 self-check
   `plan_is_jointly_feasible`), return it. Do the same when even the cheapest assignment exceeds the budget.
2. Otherwise run the frozen DCR-v3 Rescue portfolio, unchanged. Return its plan if that plan meets both limits.
3. Otherwise return DCR-v4's decision.

**Nothing new is designed or tuned.** Both parts are frozen and already measured. This replaces "DCR-v3 on top of
DCR-v1" as the paper's extension, so the extension is built on the headline method.

## Guarantees

- **No regression:** whenever the policy-internal calendars agree with the Dataset evaluator (true on every stored
  instance), DCR-v4R solves every instance that DCR-v4 or DCR-v3 solves.
- **Budget safety:** inherited from both parts. The raw cheapest-remaining invariant holds in every member.
- **Complexity:** at most one DCR-v4 run plus DCR-v3's at most 13 runs. That is at most 14 runs of the v1-class step
  loop, so O(n²m + em + nm log m). Extra runs happen only when DCR-v4's plan fails.

## Checks before CI

- `tests/test_dcr_v4_rescue.py`, on 150 random instances (300 tests pass):
  - the composition rule holds;
  - no plan of DCR-v4 or DCR-v3 is lost;
  - budget safety holds.
- A local dev run: 160/160 valid, **159/160** jointly feasible, 160/160 within budget.

## Prediction, written before the CI runs

DCR-v4R's joint feasibility should equal the union of the stored DCR-v4 and DCR-v3 results:
- dev **159/160**;
- expansion **1,857/1,890**;
- unseen **2,216/2,241 (98.9%)**.

Unseen has already been seen by both parts, so this is a reproduction check of the composition, not a new
out-of-sample test, and it must be described that way. Any deviation from the predicted counts would mean that an
internal calendar and the evaluator disagree, and it will be reported.

## Runs

Benchmark with `algos = all`, so only DCR-v4R is new, on dev, expansion and unseen; 1 repetition.
