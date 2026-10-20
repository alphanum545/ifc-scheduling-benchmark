# DCR-IFC-v0 implementation and execution protocol

Implements design `dcr_ifc_v0_design_20260907`, specification SHA-256 `52d53eefa69bb97d2d4e7b75bad805a84cc3ff95c3277a669b381aa07cb122d9`. The complete source formulation is retained in `DCR_V0_FORMULATION_PACKAGE_2026-09-07.zip`. Executed implementation commit: `7bcefcf02642b2a69b2f03f02ca6aaeee3e28f1f`; version `dcr_ifc_v0_design_20260907_impl1`.

## Policy and isolation

`algorithms/dcr_ifc/model.py` projects public inputs and computes optimistic windows, mandatory prefix capacity and fixed checkpoint/refresh epochs. `state.py` maintains exact sorted insertion calendars, shrinking domains and first/second resource alternatives. `reserve.py` implements three scaled dual certificates from exactly two projected updates and cached exclusion minima. `scheduler.py` performs exact minimax reserve-loss ranking and permanent budget-safe fallback after the first empty screen. No full-schedule lookahead, repair, baseline invocation, parameter tuning, or calibration/witness access occurs inside policy.

DCR is only in `algorithms.proposed_registry`. The frozen seven-comparator registry and 1,120-job manifest are unchanged. Energy remains evaluator-only. Admitted candidates are not completion certificates. Novelty is unverified.

## Verification

The full suite passed 347 tests before execution, including an independent slow Fraction-based oracle on 180 deterministic synthetic DAGs, direct-bound and child-cache checks on 30 cases, equality/zero-budget tests, cache invalidation, input-order determinism, the free-resource reservation example, and the admitted-but-infeasible packing negative control. Planning assignment hashes are compared with authoritative Dataset evaluation outside policy timing.

## Separate experiments

- `ifc-dcr-v0-development-v1`: exactly 160 development inputs; seed null; repetition zero.
- `ifc-dcr-v0-deployment-smoke-v1`: three engineering smoke cases (two 60-task and one 1000-task input). This expanded size coverage replaced an earlier operational suggestion to use the first three IDs; policy and primary plan did not change.
- `ifc-dcr-v0-paired-runtime-v1`: three repetitions per method per instance for DCR and unchanged BDC, alternating order by instance index plus repetition. Total 960 timing observations.

Each invocation loads inputs outside timing and executes primary DCR followed by three timing pairs. All model preprocessing, prices, caches, scheduling and output construction are timed. Final evaluation and persistence are excluded. DCR-only primary execution before timing pairs creates an asymmetric warm-up caveat; publication-quality timing needs symmetric warm-up. No CI timing is substituted for Lambda timing.

## Actual AWS execution

The isolated deployment uses a CONTAINER IMAGE, not the ZIP packaging suggested in an earlier draft. It inherits the exact original worker runtime image to preserve the Python/dependency environment. Actual settings: ap-south-2, Python 3.11.16, x86_64, 2048 MB, 2048 MB /tmp, 300 seconds, concurrency cap 100 during execution. Direct asynchronous Lambda invocation replaces SQS only for this separate experiment. The original worker, queues, result table and result objects are unchanged.

The worker verifies the canonical ZIP and extracts only the manifest and 160 development QoS / 159 development base payloads. Neither holdout nor calibration payloads are extracted or opened. It exposes only AlgorithmInput to policies. Integrity and DCR budget/parity defects abort; ordinary algorithm/evaluator exceptions become explicit failed records with no fabricated metrics.

Results are conditional, content-identified S3 objects under `results/ifc-dcr-v0-development-v1/<implementation-commit>/`, partitioned into smoke and instances. BUILD_PROVENANCE.json is embedded at /var/task and records executed source hashes and the parent image. Credentials and signed URLs must never be committed.

## Observed outcome and gates

160/160 primary executions and 960/960 timing observations succeeded. All primary schedules were independently re-evaluated and all timing scientific outcomes reproduced. DCR: 139 joint / 160 budget / 139 deadline; BDC: 120 joint / 156 budget / 120 deadline. DCR gained 24 cases and lost five relative to BDC.

Median paired runtime ratio: 1.0566234593 (target <=2 passed). Nearest-rank p95: 3.2565416361 (target <=3 FAILED). Do not relax the failed gate or change this implementation in place. No outcome-driven policy changes occurred. Preserve v0 and version future decision-preserving optimizations separately. See DCR_V0_EXECUTION_2026-09-07.md for evidence and storage locations. Main is not merged without approval.
