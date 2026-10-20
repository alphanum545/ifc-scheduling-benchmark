# DCR v1 implementation specification — 2026-09-07

Status: pre-execution specification for impl1 and admission1. The preceding recommendation is retained below as the mathematical design record. Novelty remains unverified. The 40 holdout inputs remain sealed.

## Decision

Implement **arrival-conditioned monetary reserve** as one separately versioned DCR-v1 change. Account for the direct children's resource options that a candidate actually removes through its finish time and communication delays. Use that corrected reserve in both admission and the existing minimax reserve-loss ranking, starting at the first decision.

Retain the fixed price checkpoints and refresh epochs, exact arithmetic, task priority, tie-breaking, raw-budget invariant, and permanent fallback. Do not combine comparator outputs or add repair/backtracking as part of this mechanism.

## Why this is the next justified change

The entire 160-input v0 replay reproduced the original results. All 21 failures were traced, including the five instances where BDC succeeds and v0 fails.

In **all 15 `current_reserve_exceeds_budget` failures**, the immediately preceding candidate's capacity-only bound was within budget. Its actual committed child-arrival restrictions raised the same-price-pool reserve above budget. The diagnostic independently recomputed the post-commit bound and verified equality with the corrected candidate bound at every observed non-fallback prefix in these 21 runs. This is a specific discrepancy between what v0 prices before a decision and what its state contains afterwards, not a floating-point error or an implementation deviation from its specification.

The other six failures had only one raw-budget-affordable resource at the first fallback. Five failed its capacity monetary bound; one failed its current timing window. They had spent 99.82347%–99.99997% of their budgets. The proposed change is not established as a complete explanation or cure for those six cases.

At the immediately preceding step, seven failures had a different v0-admitted alternative whose child-corrected bound remained within budget. A fixed diagnostic intervention selected one such alternative per eligible case and continued the unchanged policy. Only one of the seven fully recovered; six still missed the deadline. Eleven of the fifteen reserve-jump failures had no such alternative at that late point. The mechanism should therefore inform decisions from the start, not be sold as a last-step rescue.

Example: Montage-100, S01, compute-constrained, tight (case F11). At step 98 v0 assigns ID00097 to cloud-001. Its capacity-only bound is 227,098,015,000 nCU, below B=228,379,866,167. The child's free option disappears after the parent arrival, adding 1,842,666,900 nCU to the bound. The true same-pool bound becomes 228,940,681,900, already above budget. The one-step cloud-002 intervention yields a complete feasible schedule at cost 228,124,682,000 nCU and makespan 115,536,230 microseconds. This is a diagnostic recovery, not a v1 result or an increase in v0's 139/160 count.

## Definition

Let P be the current fixed prefix. For candidate task i on resource r at [s,f), retain v0's capacity-only hypothetical domains, denoted A-tilde_j(i,r). Define the actual one-commit domains:

\[
A_j^+(i,r)=
\begin{cases}
\{q\in\widetilde A_j(i,r): f+d_{ij}(r,q)+p_{jq}\le b_j\}, & j\in succ(i),\\
\widetilde A_j(i,r), & j\notin succ(i).
\end{cases}
\]

Existing committed-parent restrictions are already included in A-tilde. These are exactly the domains obtained by committing this candidate under the current v0 domain model; they are still optimistic about uncommitted ancestors, future packing, and contiguous free gaps.

For each of the three fixed scaled price vectors, retain v0's W_jq,l and H. Define

\[
G_l^+(i,r)=H(C_P+c_{ir})+
\sum_{j\in U\setminus\{i\}}\min_{q\in A_j^+(i,r)} W_{jq,l}
-\sum_{q,k} Z_{qk}^{(l)}K_{qk}(P)
+\sum_k Z_{rk}^{(l)}o_k.
\]

Use G-plus=max_l G_l-plus. Reject empty A-plus or G-plus > H B. Replace the old bound by G-plus in the monetary-loss fraction:

\[
P_B^+(i,r)=\frac{G^+(i,r)-G_0(P)}{HB-G_0(P)}.
\]

Use the existing exact zero-margin convention. Keep the existing time loss and lexicographic ordering `(max(time_loss,budget_loss), min(...), finish, direct_cost, resource_id)`.

Only direct-child minima change relative to v0's candidate calculation:

\[
G_l^+=\widetilde G_l+
\sum_{j\in succ(i)}
\left[\min_{q\in A_j^+}W_{jq,l}-\min_{q\in\widetilde A_j}W_{jq,l}\right].
\]

Every correction is nonnegative. The maximum must be taken **after correcting each price vector**; adding the maximum correction to the maximum old bound is generally incorrect.

## Guarantees and limits

1. Every true deadline-feasible extension of the candidate must obey the child-arrival restrictions. The same dual lower-bound proof therefore applies to the narrower domains.
2. G-plus is no smaller than the capacity-only bound and no smaller than the same-pool current bound for a locally admissible candidate. The exact loss remains nonnegative.
3. For the same price vectors, the candidate bound equals the reserve recomputed immediately after commitment. This removes the observed one-commit child-arrival reserve discontinuity. It does not prevent an increase caused by a later price refresh.
4. The independent raw minimum-cost budget invariant remains unchanged; final budget safety does not depend on successful screening.
5. Admission still does not prove that an integral, precedence-consistent, gap-feasible completion exists. Keep the original packing negative control.
6. A stronger admission check can make fallback happen earlier if the prefix is already poor. Improved feasibility is a hypothesis, not a theorem. Ranking with the corrected bound from the first task is essential to test the intended mechanism.

## Preserve the complexity target

A direct child-resource scan inside every parent-resource candidate adds O(e m²) work. Do not use that as the production implementation while claiming the v0 bound.

The frozen network offers only three tiers; for a fixed edge and source/target tier pair, transfer delay is constant across distinct resource identities. Use batched threshold sweeps:

1. Pre-sort each child's resources by duration within each target tier. Keep active-domain filtering and the three current adjusted weights.
2. Once per selected parent, sort its candidate finishes within each source tier, descending.
3. For an edge i→j and a source/target tier pair, the eligibility threshold is `b_j - candidate_finish - tier_delay`. In that candidate order it increases monotonically.
4. Sweep the target-tier resources in increasing duration, inserting active eligible options. For each price vector maintain the best two adjusted weights with distinct resource IDs. This supports excluding the candidate's own resource from the different-resource case.
5. Check the same-resource option separately, with zero communication and the candidate's capacity deletion. Take the minimum across the three target tiers and the same-resource option.
6. Accumulate the child's corrected minimum into a per-candidate, per-price-vector array; discard temporary arrays after this parent.

There are fixed numbers of tiers and price vectors. The sweep costs O(m) per edge after sorting, and sorting candidates costs O(n m log m) over the workflow. Together with unchanged capacity screening, the intended whole-policy arithmetic bound remains:

\[
O(n^2m+em+nm\log m),\qquad S=O(nm+e).
\]

This is an implementation plan and argument, not a verified v1 implementation. Parity-test the batched sweep against independent brute-force corrected minima, including asymmetric tier routes if the public interface ever permits them. Do not transfer this complexity claim to arbitrary pair-specific network delays.

## Next implementation contract

Create a new v1 package, ID, version, design document, and source freeze. Preserve v0 and opt1. First validate the corrected formulas with synthetic DAGs, equal-score distinct alternatives, zero budget, tiny deadlines, joins, same-resource communication, and candidate capacity deletion. Check that direct recomputation after a commitment equals its predicted bound with the same price pool.

Implement the batched sweep and compare it to the slow corrected oracle. Run all 160 development inputs with the frozen authoritative evaluator, then symmetric paired runtime on the original AWS configuration. Preserve median ≤2 and nearest-rank p95 ≤3 relative to unchanged BDC.

Record the full paired transition table against opt1, especially losses among the 139 already feasible inputs and the five BDC-only cases. Report all outcomes even if the change underperforms.

Predeclare three focused variants: (A) opt1 with the original capacity-only reserve; (B) corrected reserve used only for admission, with the original monetary ranking among survivors; (C) corrected reserve used for both admission and ranking. These isolate the new mechanism. They do not replace the previously pending v0 component ablations.

Complete the mechanism-level literature audit before any novelty claim. Freeze final algorithm and parameters before opening the 40 holdout inputs once. No holdout access is needed for this implementation stage.

## Frozen execution protocol

Stage 16 implements the design above in algorithms/dcr_ifc_v1. Full v1 ID dcr_ifc_v1_arrival / version dcr_ifc_v1_arrival_design_20260907_impl1. Admission-only ID dcr_ifc_v1_arrival_admission / version dcr_ifc_v1_arrival_design_20260907_admission1. No policy parameters are fitted. Original and optimized v0 remain byte-identical.

Execute both new variants on every one of the frozen 160 development instances with the pinned Dataset evaluator. Preserve full decisions, assignments, diagnostics and exact metrics. Compare all paired success transitions against opt1 and BDC, retain all regressions, and analyze every failed v1 prefix.

AWS symmetric study: four methods (full v1, admission-only, opt1, BDC), one warm-up each, four timed repetitions each, cyclic Latin square with alternating direction by sorted input index. Each method occupies every timing position exactly once per input. This yields 2560 timed observations. Use the exact original image, Python 3.11.16, x86_64, 2048 MB memory and temporary storage, 300-second timeout, ap-south-2. Three smoke cases exercise the same full timing protocol before the 160 primary jobs. For each input form the ratio of method timing medians; across all 160 inputs evaluate exact median <=2 and nearest-rank p95 <=3 against BDC. No result-driven threshold or version changes.

Main integration, holdout access and novelty claims remain outside this execution.
