# Stage 15 — DCR v0 optimization and failure investigation

Reference code: `7bcefcf02642b2a69b2f03f02ca6aaeee3e28f1f`; base branch commit `cc5ac8b45743a654297517431ba1ce79d2d5b777`.
New ID `dcr_ifc_v0_optimized`, version `dcr_ifc_v0_design_20260907_opt1`.

Capacity-screen slack fast paths and incremental same-price-pool totals preserve exact v0 policy decisions. Original DCR source and the seven comparators are unchanged. The original registry is retained; the dedicated study imports the optimization explicitly.

Verification: 567 tests; 160/160 original decision/statistics/assignment/metric parity; 139 joint, 160 budget. All 21 failures traced. All 15 reserve-over-budget failures arise from a preceding child-arrival reserve jump. Six empty screens have one affordable resource left. Seven bounded one-step probes recover one case; these are not v1 results.

AWS experiment `ifc-dcr-v0-opt1-symmetric-aws-v1`: exact original image, Python 3.11.16/x86_64/2048 MB, three methods, equal warm-up, three balanced repetitions, 1440 verified observations. Optimized/BDC median 0.5132386011, nearest-rank p95 1.1121109147, max 1.3538404110; both unchanged gates pass. Symmetric original-v0/BDC p95 3.2554082329 still fails. 163 invocations, zero errors/throttles, peak logged memory 388 MB, maximum invocation duration 189918.08 ms. Both original and new workers are now sealed at concurrency zero.

Executed source archive SHA-256 `f844c90e58909c48650170083252051533b2f6d38d3d907b4241dec571ef40f2`.
S3 prefix `<private-results-bucket>/results/ifc-dcr-v0-opt1-symmetric-aws-v1/f844c90e58909c48650170083252051533b2f6d38d3d907b4241dec571ef40f2/`.

Reproduce with `experiment.dcr_optimization_study`, `experiment.dcr_failure_diagnostics`, and `experiment.collect_dcr_optimization`. New isolated AWS handler: `deployment/aws/dcr_optimized_handler.py`. CLI outputs must go outside Git. Full reports/evidence are archived separately.

Next: arrival-conditioned monetary reserve in both screening and ranking, from the first task, using batched tier threshold sweeps. See `DCR_V1_RECOMMENDATION.md`. V1 is not implemented. Novelty, ablations, holdout and final generalization remain unverified. Holdout/calibration payloads were not opened. Main was not merged.
