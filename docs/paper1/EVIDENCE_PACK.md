# Paper 1 evidence pack: joint deadline–budget feasibility (DCR)

Built 2026-10-24 from `alphanum545/ifc-scheduling-benchmark` at commit `cc7f5b5` (results/store.csv, reference/aws-runtime.json, algorithm sources). No scheduler was rerun; every number below is recomputed from stored results by `analysis/stats.py`.

**Framing agreed:** DCR-v1 Admission is the proposed method. DCR-v3 Rescue is reported in the same paper as an extension: same complexity class (constant factor 13), slower in practice, much higher feasibility. Comparators are greedy/list heuristics only; metaheuristics go in the related work.

---

## 1. Headline results

### Expansion set (1,890 instances, all 12 algorithms valid on all cases)

| Algorithm | Joint feasible | 95% Wilson CI | Deadline met | Budget met |
|---|---:|---|---:|---:|
| DCR-v3 Rescue (extension) | 1,844 (97.6%) | 96.8–98.2% | 1,844 | 1,890 |
| **DCR-v1 Admission (proposed)** | **1,629 (86.2%)** | 84.6–87.7% | 1,629 | 1,890 |
| BDC (ω=0.5) | 1,427 (75.5%) | 73.5–77.4% | 1,435 | 1,858 |
| BDSD | 1,109 (58.7%) | 56.4–60.9% | 1,109 | 1,890 |
| DBCS | 904 (47.8%) | 45.6–50.1% | 904 | 1,890 |
| BDHEFT (α=0.5) | 852 (45.1%) | 42.8–47.3% | 934 | 1,710 |
| BDDC (ω=0.5) | 446 (23.6%) | 21.7–25.6% | 1,609 | 679 |
| HEFT-IFC | 106 (5.6%) | 4.7–6.7% | 1,890 | 106 |
| PEFT-IFC | 18 (1.0%) | 0.6–1.5% | 1,826 | 35 |

### Development set (160 instances)

| Algorithm | Joint feasible | 95% Wilson CI |
|---|---:|---|
| DCR-v3 Rescue | 157 (98.1%) | 94.6–99.4% |
| **DCR-v1 Admission** | **140 (87.5%)** | 81.5–91.8% |
| BDC (ω=0.5) | 120 (75.0%) | 67.8–81.1% |

DCR budget safety: every DCR variant met the budget on **every** instance (160/160 and 1,890/1,890). This follows from the raw minimum-cost invariant in the code (`st.spent + st.raw_reserve ≤ B` is asserted after every commit), so it can be stated as a guarantee, not only an observation. Every DCR failure is a deadline miss.

**Deadline-only and budget-only rows (sanity, not contributions).** HEFT meets the deadline on 1,890/1,890 (all three QoS levels), because the generator sets D ≥ T_fast. The cheapest assignment always meets the budget. Separate deadline-only or budget-only feasibility therefore cannot discriminate between algorithms on this benchmark. Report these two rows in one sentence, and say this is why the joint problem is the one studied.

## 2. Significance (exact McNemar on paired outcomes, Holm-corrected over the 7 comparators)

| DCR-v1 Admission vs | Only DCR | Only other | Δ (pp) | p (Holm), expansion | p (Holm), dev |
|---|---:|---:|---:|---:|---:|
| BDC | 255 | 53 | +10.7 | 7.6e-33 | 1.8e-04 |
| BDSD | 584 | 64 | +27.5 | 1.1e-105 | 7.6e-11 |
| DBCS | 726 | 1 | +38.4 | 8.3e-216 | 3.3e-19 |
| BDHEFT | 790 | 13 | +41.1 | 9.6e-214 | 2.7e-20 |
| BDDC | 1,183 | 0 | +62.6 | <1e-300 | 5.2e-29 |
| HEFT / PEFT | 1,523 / 1,611 | 0 / 0 | +80.6 / +85.2 | <1e-300 | ≤2.2e-39 |

The "only DCR" / "only other" counts are the expansion set; the dev counts are in `statistics.md`. Every comparison is significant on both sets after correction.

**Where the gain comes from (QoS level, DCR-v1 Admission vs BDC, expansion):**

| QoS | DCR-v1 | BDC | Only DCR | Only BDC | p |
|---|---:|---:|---:|---:|---:|
| relaxed | 630/630 | 630/630 | 0 | 0 | 1 |
| moderate | 554/630 | 556/630 | 27 | 29 | 0.89 (no difference) |
| tight | 445/630 | 241/630 | 228 | 24 | 6.9e-43 |

State this honestly in the paper: the advantage is entirely under tight constraints; at relaxed and moderate QoS, DCR and BDC are statistically tied. The dev set shows the same pattern (tight 39 vs 21, p = 1.2e-04; moderate 47 vs 45, p = 0.69).

**DCR-v3 Rescue vs DCR-v1 Admission:** 215 cases only v3, **0 cases only v1** (expansion), 17 vs 0 (dev); p = 3.8e-65. v3 never loses a case v1 solves. This follows from the design (it returns v1's decision whenever v1's plan is feasible; see §4).

**v3 in-sample caveat, quantified.** v3's portfolio was designed on the 24 core dev cases. Excluding them, v3 solves 134/136 dev cases (98.5%), against v1 120/136 and BDC 101/136. On the 1,890 expansion configurations (never seen during design) it solves 97.6%. So the extension result is not an artefact of its design cases.

## 3. Secondary quality where both are jointly feasible (expansion, DCR-v1 Admission / other)

| Against | Metric | n | Median ratio | 95% bootstrap CI | Wilcoxon p |
|---|---|---:|---:|---|---:|
| BDC | makespan | 1,374 | **0.844** | 0.834–0.854 | 3.0e-144 |
| BDC | compute cost | 1,374 | 1.010 | 1.008–1.012 | 6.3e-41 |
| BDSD | makespan | 1,045 | 0.864 | 0.835–0.894 | 2.9e-11 |
| BDSD | compute cost | 1,045 | 1.161 | 1.146–1.193 | 3.4e-96 |
| DBCS | makespan | 903 | 0.729 | 0.683–0.773 | 3.0e-79 |
| DBCS | compute cost | 903 | 0.931 | 0.921–0.940 | 4.4e-149 |
| BDHEFT | makespan | 839 | 1.000 | 0.991–1.013 | 7.7e-03 |
| BDHEFT | compute cost | 839 | 0.959 | 0.947–0.969 | 1.6e-84 |

Wording: DCR's schedules are 16% shorter than BDC's at about 1% higher cost. Against BDSD they are shorter but 16% more expensive. Both stay within budget, so this is a trade-off inside the feasible region, not a weakness. It is secondary to feasibility.

## 4. Complexity

Notation: n tasks, e edges, m resources. A route lookup is O(1) (three fixed tiers, the delay for a tier pair is constant).

### Theorem 1 (DCR-v1). One run of DCR-v1 (Admission or full ranking) takes O(n²m + em + nm log m) time and O(nm + e) space.

Proof sketch, per scheduling step (there are n steps); every line maps to `algorithms/dcr_ifc_v1/scheduler.py` and the State/ReservePool code:

| Operation | Cost per step | Total over n steps |
|---|---|---|
| Choose the ready task (`choose_task`, min over ready set) | O(n) | O(n²) |
| Insertion slot on every resource (scan of a sorted calendar of ≤ n intervals) | O(nm) | O(n²m) |
| Raw-budget filter | O(m) | O(nm) |
| Price-pool rebuild, only at the 4 fixed epochs (3 price vectors, weights and one sort per task) | — | O(nm log m) |
| Incremental reserve refresh (removed task + dirty domains; first/second cursors only advance) | O(n + m) amortized | O(n² + nm) |
| Capacity deletions per candidate (one pass over unscheduled tasks) | O(nm) | O(n²m) |
| Child-arrival sweep (`prepare`): candidates sorted once per parent; per child, 3×3 tier pairs, monotone cursor over m targets | O(m log m + outdeg(i)·m) | O(nm log m + em) |
| Candidate bound: 3 price vectors × deleted tasks (≤ n) | O(nm) | O(n²m) |
| Commit: calendar insert, window update over unscheduled tasks, child readiness over m resources | O(n + outdeg(i)·m) | O(n² + em) |
| Preprocessing (windows a, b, h; 4-checkpoint table g) | — | O(nm + e) |

The sum is O(n²m + em + nm log m). The child-arrival correction adds only the O(em) sweep, because the brute-force O(em²) child scan is replaced by the batched threshold sweep (spec §"Preserve the complexity target"). Space is dominated by the n×m tables (p, c, g, windows, activity) and the edge list.

### Theorem 2 (DCR-v3 Rescue). One run of DCR-v3 takes at most 13 × O(n²m + em + nm log m) = O(n²m + em + nm log m) time.

Proof, from `ifc_algorithms/proposed/dcr_v3_rescue.py`:

1. **Fixed portfolio size.** The portfolio is constructed once and never grows: champion (DCR-v1 Admission), Graded, Sparing, Task-Pacing at 5 fixed α values, and Pressure-Gated at 5 fixed κ values. That is K = 1 + 2 + 5 + 5 = 13, independent of the instance.
2. **Each member is in the same class.** Every non-champion member is `_DCRV2Base`, which repeats the champion's step loop statement for statement. It differs only in (a) one filter over the already-admitted candidates of a step, O(|screened|) ≤ O(m) (task pacing: one integer comparison per candidate; pressure gating: one comparison and one min); and (b) the choice made when nothing is admitted, O(m) (relaxed, sparing or champion fallback rule). The Graded member may keep screening when the reserve exceeds the budget, but that is the champion's screening branch, which the bound of Theorem 1 already assumes for every step. Extra cost per member: O(nm), which is absorbed. No member adds price vectors, refresh epochs or schedule rebuilds.
3. **Selection is O(1) per member.** The feasibility self-check compares the member's own internal makespan and cost with D and B.
4. **Early stop only reduces work.** A member aborts as soon as a committed finish exceeds the task's latest finish b_i = D − h_i, which provably implies makespan > D.

Hence T_v3 ≤ 13·T_v1-class + O(13) = O(n²m + em + nm log m). ∎

**Corollary (no regression).** If DCR-v1 Admission's plan is jointly feasible, v3 returns exactly that decision. So v3's feasible set contains v1's whenever the internal calendar agrees with the evaluator, which it did on all 2,050 instances (0 cases where only v1 succeeded).

**Practical cost (to report next to the theorem).** v3 runs extra members only when v1 fails (about 14% of expansion cases). Dev runtime vs BDC, one instance at a time: median 0.69×, p95 3.13×, max 8.18×. Say it plainly: same class, but up to ≈13× more work on the hard cases where v1 fails.

### Comparator complexity: state both forms

| Algorithm | Paper's claim | As implemented under IFC routing |
|---|---|---|
| HEFT, PEFT | O(n²m) | O(em² + n²m) |
| BDHEFT | O(n²) | O(em² + n²m) |
| DBCS | O(n²m) | O(em² + n²m) |
| BDSD | O(n²m) | O(em² + em) |
| BDDC, BDC | O(n²) | O(em² + n²m) |
| DCR-v1 | — | O(n²m + em + nm log m) |
| DCR-v3 | — | ≤ 13 × DCR-v1 |

The comparators' em² term comes from upward ranks with route-dependent average communication over all resource pairs. DCR has no such term, so the comparators are not asymptotically cheaper.

## 5. Runtime (measured)

**AWS symmetric study** (`reference/aws-runtime.json`): 160 dev cases, ap-south-2, Python 3.11.16, x86_64, 2,048 MB, cyclic Latin-square order. The paired ratio is the median of each method's repeated timings, divided by BDC's.

| Method | Median ratio to BDC | p95 (nearest rank) | Max |
|---|---:|---:|---:|
| **DCR-v1 Admission** | **0.653** | **1.308** | 1.51 |
| DCR-v1 full ranking | 0.649 | 1.297 | 1.50 |
| DCR-v0 optimized | 0.523 | 1.129 | 1.37 |

Both of the spec's pre-registered gates are passed (median ≤ 2, p95 ≤ 3). Use this as the runtime table for v1.

**GitHub runners, dev set** (155 cases run one at a time, 2 repetitions, every pair on the same CPU model) agree with the AWS study: v1 Admission median 0.594× (95% CI 0.519–0.688), p95 1.195×; v3 median 0.689×, p95 3.13×.

**Do not use the expansion run's runtimes.** That run used 4 parallel processes per machine with 1 repetition, so the timings include CPU contention. Its feasibility and quality numbers are unaffected, because the algorithms are deterministic and replay-checked.

## 6. Mechanism ablation, and what it means for the novelty claim

The DCR-v1 spec pre-registered three variants. All three are already in the stored results:

| Variant | Algorithm | Expansion joint | Dev joint |
|---|---|---:|---:|
| A: capacity-only reserve | DCR-v0 optimized | 1,619 | 139 |
| B: child-arrival reserve in admission only | **DCR-v1 Admission** | **1,629** | **140** |
| C: child-arrival reserve in admission + ranking | DCR-v1 full | 1,627 | 139 |

B vs A: 10 gained, 0 lost on expansion, exact p = 0.002. On dev, 1 gained and 0 lost (not significant).

**Consequence: be careful about where the paper puts its weight.** The child-arrival correction is a real and statistically supported improvement, but it is small (+0.5 pp). Almost all of the gain over BDC (+10.7 pp) is already present in the DCR core: DCR-v0 vs BDC is 247 vs 55 on expansion. The contribution should therefore be framed as **the DCR framework** (priced reserve screening plus minimax slack-loss ranking), with the exact child-arrival correction as its refinement. It should not be sold as "the child-arrival correction beats BDC".

**This made one ablation essential (now run; results in §6b):** the components inside the DCR core. Without it, a reviewer cannot tell whether the priced reserve, the minimax rule, or both produce the gain. Suggested predeclared variants, each a small subclass of DCR-v1 Admission, run in CI on dev + expansion:

1. **No priced reserve:** admission by the raw cheapest-remaining reserve only. This is the classic prior-art mechanism, so it directly separates DCR from it.
2. **Time-loss-only ranking:** among admitted candidates, earliest finish.
3. **Budget-loss-only ranking.**
4. **Weighted sum** 0.5·time + 0.5·budget instead of the minimax rule. This shows that the parameter-free minimax rule matters compared with the ω/α weights used by BDC, BDDC and BDHEFT.
5. **Zero prices** (one price vector, H·c only): checks whether the capacity checkpoints add anything.

## 6b. Component ablation results (run 2026-10-24, protocol predeclared in `docs/proposed/ABLATIONS_PAPER1.md`)

The harness is faithful: the control variant's schedule equals DCR-v1 Admission's stored schedule on **160/160** dev and **1,890/1,890** expansion instances. Each variant changes exactly one component. The table compares each with control using exact McNemar tests, Holm-corrected over the five variants.

| Variant | Dev joint | Expansion joint | Δ vs control | Only control / only variant | p (Holm) | Tight, expansion |
|---|---:|---:|---:|---:|---:|---:|
| **Control = DCR-v1 Admission** | 140 (87.5%) | 1,629 (86.2%) | | | | 445/630 |
| No priced reserve (raw cheapest-remaining only) | 137 | 1,579 (83.5%) | −2.6 pp | 53 / 3 | 2.4e-12 | 398/630 |
| Zero dual prices | 140 | 1,629 (86.2%) | 0.0 | **0 / 0** | 1 | 445/630 |
| Time-only ranking | 83 | 984 (52.1%) | −34.1 pp | 648 / 3 | 4.9e-188 | 336/630 |
| Budget-only ranking | 82 | 961 (50.8%) | −35.3 pp | 727 / 59 | 1.1e-146 | 111/630 |
| Weighted-sum ranking 0.5/0.5 | 142 | 1,659 (87.8%) | **+1.6 pp** | 17 / 47 | 4.5e-04 | 447/630 |
| *(BDC, for reference)* | 120 | 1,427 (75.5%) | | | | 241/630 |

**What this shows:**
1. **Balancing time and budget is the core mechanism.** Ranking on either loss alone collapses feasibility by about 35 pp. The decisive idea is to score each placement by both its normalized time-slack and its normalized budget-slack consumption.
2. **The deadline-aware reserve helps, modestly.** Replacing it with the classic cheapest-remaining reserve loses 2.6 pp overall (53 vs 3 cases) and 47 tight cases (−7.5 pp). That is real and significant, but secondary.
3. **The dual prices are inert on this benchmark.** With zero prices DCR makes exactly the same decisions on all 2,050 instances. The capacity checkpoints never change a choice.
4. **The minimax rule is not better than a 0.5/0.5 weighted sum.** The weighted sum is slightly but significantly better on expansion (+1.6 pp, p = 4.5e-4) and equal under tight QoS. So "parameter-free minimax beats weights" cannot be claimed.
5. **Even the weakest working variant beats BDC.** The no-reserve variant reaches 83.5% against BDC's 75.5%.

**Consequence for the novelty claim (replaces items 1–2 of §7).** The supportable contribution is:
- normalized slack-consumption balancing, in which each placement is scored by the fraction of remaining deadline slack and the fraction of remaining budget slack it consumes, combined;
- plus admission by a deadline-aware cheapest-completion reserve with the exact child-arrival correction;
- plus a budget-safety guarantee.

The dual-price tightening and the specific minimax form should be presented as design choices with honest ablation results, not as sources of the gain.

## 7. Novelty: bounded check and the claim to make

Search done: deadline-and-budget workflow heuristics, cheapest-remaining-cost reserves, dual-price/Lagrangian bounds in DAG scheduling, minimax slack ranking, IFC/fog 2024–2026. The comparator audits in `docs/paper_audits/` were cross-read. The check was time-boxed, not exhaustive.

**Prior art the paper must acknowledge (not novel in DCR):**
- Splitting the problem into sub-deadlines and sub-budgets: BDDC (level budgets), BDHEFT (spare budget/deadline), BDSD (remaining budget).
- Using the entire remaining budget at each step: BDC.
- Weighted time–cost "quality" scores, with ξ zeroing infeasible options: DBCS/DBWS, Q = TimeQ·(1 − CF) + CostQ·CF.
- Reserving the cheapest cost of unscheduled tasks, and admission control against a workflow budget: the budget-deadline admission-control line (Zheng & Sakellariou, JGC 2013) and budget-constrained makespan heuristics. DCR's raw invariant is of this type, so claim it as a property, not as novelty.
- Lagrangian/dual bounds are standard in project and job-shop scheduling, but there they are used in exact or iterative solvers, not as a per-placement screen inside a one-pass list scheduler.

**What appears new (claim this, worded with "to the best of our knowledge"):**
1. **Deadline- and capacity-aware priced reserve as a per-candidate admission certificate.** Each tentative placement is screened with a lower bound on the cheapest completion cost of the unscheduled tasks. The bound counts only resources that can still meet each task's latest finish and the per-resource capacity checkpoints, and it is tightened by three fixed dual price vectors. A placement is admitted only if this bound fits the budget. The prior reserves above ignore time windows and capacity.
2. **Parameter-free minimax slack-loss ranking.** Admitted candidates are ranked by max(fraction of remaining time slack consumed, fraction of remaining budget slack consumed). All comparators use a tunable weight (ω, α, CF) instead.
3. **Exact child-arrival correction** of that reserve, inside the same complexity bound (batched three-tier sweep instead of an O(em²) scan).
4. **Constant-factor rescue portfolio (v3)** that provably never loses a v1 success.

Suggested contribution sentence:

> We propose DCR, a list scheduler for IoT–Fog–Cloud workflows under a joint deadline and budget that admits each placement only if a deadline- and capacity-aware priced lower bound on the remaining cost still fits the budget, and ranks admitted placements by the larger of their normalized time-slack and budget-slack consumption, with no weighting parameter. DCR never exceeds the budget by construction and runs in O(n²m + em + nm log m).

Two short checks to do before submission, about 1–2 hours in total rather than days: search Google Scholar for "lower bound" AND "budget" AND "list scheduling" AND workflow since 2022, and read the related-work sections of the two most recent IFC deadline–budget papers you cite. If neither shows a per-placement priced lower-bound screen, the claim stands as worded.

## 7b. Novelty check: final verdict (completed 2026-10-24; supersedes §7 and the claim note in §6b)

**Sources checked:**
- the audited comparator papers in `docs/paper_audits/`: BDHEFT (Verma & Kaushal 2015), DBCS (Arabnejad, Barbosa & Prodan 2016), BDSD (Sun et al. 2019), BDDC/BDC (Taghinezhad-Niar et al. 2021);
- the budget-aware workflow algorithms from ICL/UTK (2018);
- concurrent-workflow budget–deadline scheduling (Soft Computing 2018, abstract only);
- DDBWS (J. Supercomputing 2021, abstract only);
- targeted searches for 2023–2026 IFC/fog deadline–budget heuristics. Recent IFC work is mostly metaheuristic or RL, for example RIGEO (2026); it is related work, not prior art for DCR's mechanism.

**DCR component → closest prior art → status:**

| DCR component | Closest prior art | Status |
|---|---|---|
| Never exceeding the budget, via a cheapest-remaining reserve (raw invariant) | **DBCS:** ΔCost = unconsumed budget − cheapest cost of the remaining tasks, a hard limit. BHEFT/BDHEFT use average remaining cost; BDSD uses rb/l; ICL 2018 uses up-front reserves | **Not new.** State it as a property shared with DBCS. |
| Combining normalized time and cost scores for resource selection | BDC/BDDC: ω·TQ + (1−ω)·CQ, normalized by sub-deadline or remaining budget. DBCS: TimeQ/CostQ normalized over the candidates' range | **Not new.** The ablation confirms that the aggregation form (minimax or weighted sum) is not the source of the gain. |
| Per-task time windows from the deadline (latest finish = D − critical tail) | Sub-deadlines in DBCS, BDSD and BDDC; latest-finish times in the PCP/IC-PCP family | **Not new** as a concept. |
| **Deadline-aware cheapest-completion reserve:** a lower bound on the remaining cost that counts, for each unscheduled task, only options that can still meet its latest finish, after the candidate's capacity occupation and exact child-arrival delays. It is used both as a per-placement admission test and as the base of the budget slack | Every reserve found is **deadline-blind**: DBCS cheapest-remaining, BHEFT average, BDSD rb/l, ICL proportional shares | **New, as far as this check found.** Measured contribution: +2.6 pp overall (53 vs 3 cases) and +7.5 pp at tight QoS, compared with a DBCS-style deadline-blind reserve (§6b). |
| **Slack-consumption scoring:** each placement is scored by the fraction of the task's remaining time slack, up to its latest finish, and the fraction of the remaining budget slack, above the deadline-aware reserve, that it consumes | Closest is BDC's TQ/CQ, but BDC normalizes by sub-deadline and remaining budget with no future-cost reserve. DBCS normalizes over the candidates' min–max range | **New as a formulation, but its separate effect is not isolated.** The no-reserve ablation still reaches 83.5% against DBCS's 47.8% and BDC's 75.5%, with the same reserve type as DBCS. That suggests the slack-relative scoring matters, but we did not ablate DCR's normalization directly against DBCS-style or BDC-style normalization. |
| Exact child-arrival correction inside the same complexity bound (batched three-tier sweep) | None found | **New, small:** +0.5 pp (§6). |
| Dual price vectors on capacity checkpoints | Lagrangian bounds exist in exact project-scheduling methods | Not a contribution: inert on this benchmark (§6b). |
| v3: a constant-size rescue portfolio that never loses a v1 success | Algorithm portfolios are generic | Engineering extension: the guarantee and the measured gain are reportable, but this is not a novelty claim. |

**Verdict:** the novelty is real but modest. It rests on one mechanism, the **deadline-aware reserve**. The budget reserve itself is coupled to the deadline windows, so a placement is admitted only while the cheapest *timely* completion still fits the budget. Each placement is then scored by how much of these feasibility-preserving time and budget slacks it uses. Prior deadline–budget list heuristics reserve budget without regard to the deadline, and score against sub-deadlines or candidate ranges. That is enough for a solid journal paper whose main weight is the strong, reproducible empirical evidence (§1–§2, §8b). It is not a new paradigm, and the paper should not present it as one.

**Claim wording to use:**

> To the best of our knowledge, existing deadline- and budget-constrained workflow list heuristics reserve budget for unscheduled tasks without regard to the deadline (cheapest, average or proportional remaining cost). DCR instead admits a placement only if a *deadline-aware* lower bound on the cost of completing the remaining tasks — counting only resources on which each task can still meet its latest finish time, including the candidate's effect on its children's arrival — still fits the budget, and ranks admitted placements by the fraction of the remaining time slack and of the remaining budget slack they consume. Like DBCS, DCR never exceeds the budget; unlike it, its reserve also protects the deadline.

**Claims to avoid:**
- "first algorithm guaranteeing budget compliance" (DBCS already does);
- "parameter-free ranking is superior to weighted rules" (the ablation contradicts it);
- "dual-priced reserve" as a source of gain (the prices are inert);
- any "novel" claim for v3's portfolio.

**Related-work paragraph must cite and contrast:**
- DBCS: the same hard budget guarantee, but a deadline-blind reserve and candidate-range normalization;
- BHEFT/BDHEFT: average-cost spare budget;
- BDSD: per-task remaining-budget share;
- BDC/BDDC: weighted, sub-deadline-normalized quality;
- the ICL budget-aware algorithms: up-front reserves, not deadline-aware.

**One optional ablation would make the slack-scoring claim fully attributable.** Replace DCR's slack-relative losses with BDC-style normalization (sub-deadline and remaining budget) while keeping DCR's deadline-aware reserve. It is the same kind of run as the §6b ablations. It is not required: without it, state the scoring formulation as part of the method rather than as a separately proven contribution.

## 8. Related work: handling metaheuristics

Paragraph you can adapt:

> A large body of work addresses deadline- and budget-constrained workflow scheduling with population-based metaheuristics (genetic algorithms, PSO, ACO and hybrids, e.g. DB-ACO and PSO-SA, 2024). These methods search over many complete schedules and their running time depends on population size and iteration count, typically orders of magnitude above a single list-scheduling pass; results also vary with the random seed. DCR belongs to the other family: deterministic, single-pass list heuristics with polynomial worst-case bounds, suitable for online or repeated planning at IoT/fog decision points. We therefore compare DCR with the established deterministic deadline–budget heuristics (BDHEFT, DBCS, BDSD, BDDC, BDC) and with HEFT/PEFT as constraint-agnostic references, and we discuss metaheuristics only as related work. A metaheuristic could use DCR as a seeding or repair operator; we leave this to future work.

The audits `docs/paper_audits/DB_ACO_2024.md` and `PSO_SA_2024.md` already exist and can supply their descriptions for the survey.

## 8b. Supporting experiments (run 2026-10-24, protocols fixed beforehand in `docs/proposed/EXPERIMENTS_PAPER1.md`)

The algorithms were frozen before these runs: DCR-v1 Admission is the headline method and DCR-v3 Rescue the extension. The replay check still reports 0 mismatches after all runs.

### A. Unseen-workflow test (`ifc-unseen-v1`)

The set has 2,241 instances on 83 DAGs that no algorithm was designed on: 4 new families and 35 new replicates. It was frozen before any run, run once, and all 12 algorithms are valid on all instances.

| Algorithm | Joint feasible | 95% CI |
|---|---:|---|
| DCR-v3 Rescue | 2,208 (98.5%) | 97.9–98.9% |
| **DCR-v1 Admission** | **1,905 (85.0%)** | 83.5–86.4% |
| BDC | 1,610 (71.8%) | 69.9–73.7% |
| BDSD / DBCS / BDHEFT / BDDC | 57.7% / 51.9% / 46.8% / 17.9% | |
| HEFT / PEFT | 6.0% / 0.4% | |

**Paired tests (exact McNemar, Holm-corrected):**
- DCR-v1 vs BDC: 343 cases only DCR solves, 48 only BDC solves, p = 4.9e-56.
- DCR-v1 vs BDSD: 727 vs 115.
- DCR-v1 vs DBCS: 745 vs 2.
- DCR-v1 vs BDHEFT: 862 vs 6.
- **DCR-v3 vs DCR-v1:** 303 cases only v3 solves, **0 only v1 solves**.

**Breakdowns:**
- **By source:** on the new families DCR-v1 reaches 83.0% against BDC's 73.3% (156 vs 30 cases). On the new replicates it reaches 87.7% against 69.8% (187 vs 18).
- **By family:** DCR-v1 is ahead of BDC in every family. The smallest margin is 1000Genome (76.2% vs 73.0%, 41 vs 29 cases).
- **By QoS level:**
  - tight: 73.2% against 39.1% (265 vs 10);
  - moderate: 81.8% against 76.4% (78 vs 38). On expansion moderate was a tie, so this is a new, modest gain;
  - relaxed: 100% for both.
- **Quality where both are feasible:** DCR-v1's makespan is 0.81× BDC's and its cost 1.015×, the same pattern as on dev and expansion.

**Interpretation:** the dev and expansion findings transfer to unseen workflow structures. This replaces the 40-instance holdout as the out-of-sample evidence.

### B. Tuned comparators (weights 0.1, 0.3, 0.5, 0.7, 0.9; expansion, 1,890 instances)

| Comparator | Weight chosen on dev | Its expansion joint feasibility | Best weight on expansion (oracle) | Per-instance best over all 5 weights | DCR-v1 Admission |
|---|---:|---:|---:|---:|---:|
| BDC (ω) | 0.5 | 1,427 | 1,427 (0.5) | 1,535 | **1,629** |
| BDDC (ω) | 0.1 | 1,021 | 1,021 (0.1) | 1,223 | **1,629** |
| BDHEFT (α) | 0.1 | 1,019 | 1,019 (0.1) | 1,236 | **1,629** |

- **Each comparator at its dev-tuned weight:** DCR solves 255 vs 53 cases against BDC, 634 vs 26 against BDDC and 641 vs 31 against BDHEFT. All p < 1e-32.
- **Against the per-instance best over all five weights,** an oracle no real comparator could use, DCR is still ahead (1,629 vs 1,535 for BDC; 194 vs 100 cases).
- ω = 0.5 turns out to be BDC's best weight, so the untuned-baseline objection does not apply. BDDC and BDHEFT improve a lot at 0.1, from 446 to 1,021 and from 852 to 1,019, but remain far below DCR.

### C. Deadline × budget tightness grid (`ifc-grid-v1`)

The grid uses the 159 dev bases × 25 cells, 3,975 instances in all. See `grid_heatmap.png` and `grid_heatmap.pdf`.

- **Whole grid:** DCR-v1 Admission 82.4%, BDC 68.9%, DCR-v3 97.9%.
- **DCR-v1 vs BDC per cell:** significantly better in **15 of 25** cells and never significantly worse. The gain is largest at the tightest deadline fraction (+37 to +45 pp) and when the budget is tight at any deadline (β = 1/10 column: +10 to +37 pp). It is zero when both constraints are loose.
- **A property to explain:** feasibility is not monotone in the deadline fraction (for DCR, BDC and DCR-v3 the α = 1/20 row is harder than α = 1/100; BDSD, which does not reserve budget, shows the opposite). The budget is anchored on the cheapest calibration schedule that meets the deadline, so a very tight deadline also raises the budget. This comes from the calibration design, not from any algorithm.

### D. Robustness to noise (dev, 160 instances × 12 algorithms × 30 seeded perturbations; 0 errors)

| Algorithm | Nominal | ±10% | ±20% | ±30% | Nominally feasible schedules that stay feasible (±10/20/30%) |
|---|---:|---:|---:|---:|---|
| DCR-v3 Rescue | 98.1 | **78.0** | **75.1** | **67.2** | 79 / 76 / 68% |
| DCR-v1 Admission | 87.5 | 70.6 | 68.6 | 61.8 | 81 / 78 / 70% |
| BDC | 75.0 | 68.9 | 64.3 | 62.4 | 92 / 85 / 82% |
| BDSD | 58.8 | 58.2 | 57.9 | 57.6 | 99 / 98 / 98% |

The figures are joint-feasibility percentages of all dev instances, averaged over draws.

**This is an honest weakness, and the paper should say it.**
- DCR keeps the highest feasibility under ±10% and ±20% noise, and v3 is best at every noise level.
- But DCR's schedules are tighter: it spends about 98% of the budget, against BDC's 95%. So a smaller share of its schedules survives noise, and at ±30% DCR-v1 and BDC tie (61.8% vs 62.4%).
- **Framing:** DCR turns slack into feasibility. Under heavy uncertainty, either add a safety margin (schedule against a slightly reduced D and B) or use v3.
- Testing a margin variant would be a natural follow-up experiment, but it was not part of the frozen protocol.

**Placement** (share of tasks / busy time / compute cost; full table in `robust.md`): DCR-v1 puts 37% of tasks on IoT, 41% on fog and 22% on cloud. Cloud carries 60% of the compute cost. BDC's placement is similar (35 / 37 / 28%), so DCR's advantage is not explained by a different tier preference.

### E. Exact CP-SAT check (all 293 sixty-task dev and expansion instances, 120 s each)

- **Outcomes:** 277 proved feasible, with every found schedule confirmed by the evaluator. 16 reached the time limit. **None was proved infeasible.**
- **Of the 277 proved feasible:**
  - DCR-v3 solves 274;
  - DCR-v1 Admission solves 254 (91.7%);
  - BDC solves 185 (66.8%);
  - BDSD solves 158 (57.0%).
- **Consistency:** no instance proved infeasible was solved by a heuristic.
- **Interpretation:** at small scale almost every instance is solvable. DCR-v1's misses are real heuristic misses, which v3 mostly closes. Exact search does not scale to 1,000 tasks, so this calibrates the heuristics' optimality gap only at n = 60.

## 9. Threats to validity (put these in the paper; reviewers will raise them anyway)

1. **The 40-instance holdout was not evaluated.** It remains sealed, because the checksums needed to verify it are on S3. The frozen 2,241-instance unseen-workflow set (§8b.A) is the out-of-sample evidence instead. It is stronger, because it includes four application families absent from the design data.
2. **BDC and BDDC are major IFC adaptations.** Billing cycles and elastic provisioning are not preserved. The weight sweep (§8b.B) shows ω = 0.5 is BDC's best weight, and the comparisons still hold at each comparator's best weight.
3. **The v3 portfolio was designed on 24 dev cases.** This is mitigated by:
   - the 134/136 result on the dev cases outside its design set;
   - 97.6% on expansion;
   - 98.5% on unseen workflows.
4. **Python implementations.** Runtime is reported as paired ratios on the same machine, plus complexity bounds.
5. **Robustness:** DCR's advantage shrinks under heavy runtime and bandwidth noise (§8b.D). Report it.
6. **Calibration-dependent tightness:** the deadline-conditioned budget makes feasibility non-monotone in α (§8b.C).

## 10. Status

| Item | Status |
|---|---|
| Feasibility, significance, breakdowns, quality, AWS runtime, complexity proofs | **Done** |
| Mechanism ablations (A/B/C and the five component variants) | **Done** (§6, §6b) |
| Unseen-workflow test, tuned comparators, tightness grid, robustness, exact check, placement | **Done** (§8b) |
| Clean expansion runtime study | Optional (the AWS dev study covers v1) |
| 40-instance holdout | Replaced by the unseen set. Run it only if the S3 checksums are recovered |
| Two final novelty spot checks (§7) | **Done** (§7b) |
| **Scoring ablation**: DCR reserve with BDC-style normalization instead of slack-relative losses (§7b) | **Pending.** Agreed; run when the GitHub runners are free (dev + expansion, same protocol as §6b) |
| Writing | Next |
