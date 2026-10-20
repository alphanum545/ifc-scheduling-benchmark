# BDHEFT 2015 — paper-to-code audit

## Bibliographic identity

- **Algorithm:** BDHEFT — Budget and Deadline Constrained Heuristic based upon HEFT
- **Paper:** Amandeep Verma and Sakshi Kaushal, *Cost-Time Efficient Scheduling Plan for Executing Workflows in the Cloud*
- **Venue:** Journal of Grid Computing, 13, 495–506
- **Year:** 2015
- **DOI:** `10.1007/s10723-015-9344-9`
- **Primary source audited:** author-uploaded full article, not an abstract or secondary implementation

## Original scheduling problem

The paper schedules a single scientific workflow represented by a DAG onto heterogeneous cloud resources while attempting to minimize execution time and execution cost under a user-supplied budget `B` and deadline `D`.

## Original infrastructure model

- `m` heterogeneous computational resources with different processing powers and prices.
- Every resource is assumed able to execute every workflow task.
- Processing power is expressed in MIPS.
- Pay-as-you-go execution pricing.
- Resources are assumed in the same physical region.
- Data-storage and data-transfer monetary cost are zero.
- Communication **time** between dependent tasks mapped to different resources is considered.
- Average bandwidth is assumed approximately equal across resources.

## Original workflow model

- DAG `G(T,E)` with precedence edges.
- Task work is expressed in MI.
- Entry tasks have no parents; exit tasks have no children.
- Execution time on resource `p`, Eq. (1): `ET(i,p) = z_i / PP_p`.
- Execution cost, Eq. (2): `EC(i,p) = mu_p * ET(i,p)`.

## Task priority rule

BDHEFT inherits HEFT upward rank. For task `i`, Eq. (3):

`rank(i) = avg_ET(i) + max_{j in succ(i)}(avg_comm(i,j) + rank(j))`.

Tasks are considered in non-increasing/descending rank order.

## Earliest-time model

The paper defines resource availability `avail(p)` and uses:

- entry task: `EST(entry,p) = avail(p)`, Eq. (4),
- other task: `EST(i,p) = max(avail(p), max_parent(AFT(parent) + ct(parent,i)))`, Eq. (5),
- intended Eq. (6): `EFT(i,p) = ET(i,p) + EST(i,p)`.

The printed/extracted Eq. (6) labels the left side as `EST`; the surrounding prose identifies it as the EFT recurrence. The implementation follows the mathematically and textually consistent EFT interpretation.

The paper describes `avail(p)` as the time the resource is ready. It does not describe idle-gap insertion for the cloud algorithm. The decision heuristic therefore uses append/ready-time availability, while the benchmark's authoritative post-decision evaluator remains insertion-based for cross-algorithm fairness.

## Deadline and budget allocation

Let tasks be in BDHEFT planning order and let position `i` be the current task. Let:

- `c_k` / `e_k` be actual execution cost / execution time of already allocated tasks,
- `avg_c_j` / `avg_e_j` be average execution cost / execution time of current and unallocated tasks across resources.

The equations audited from the paper are:

`SWB_i = B - sum_{k < i}(c_k) - sum_{j >= i}(avg_c_j)`  — Eq. (8)

`SWD_i = D - sum_{k < i}(e_k) - sum_{j >= i}(avg_e_j)`  — Eq. (9)

`BAF_i = avg_c_i / sum_{j >= i}(avg_c_j)` if `SWB_i >= 0`, otherwise `0` — Eq. (10)

`DAF_i = avg_e_i / sum_{j >= i}(avg_e_j)` if `SWD_i >= 0`, otherwise `0` — Eq. (11)

`CTB_i = avg_c_i + SWB_i * BAF_i` — Eq. (12)

`CTD_i = avg_e_i + SWD_i * DAF_i` — Eq. (13)

The article states that SWB/CTB/BAF are inherited from BHEFT and introduces SWD/CTD/DAF symmetrically. The PDF text extraction damages some summation indices, so the remaining-task indexing is cross-checked against the cited primary BHEFT definition.

**Paper inconsistency:** Fig. 2 says CTB/CTD are computed with Eqs. (10) and (11), but those numbered equations are BAF/DAF; CTB/CTD are explicitly Eqs. (12) and (13). The implementation follows the displayed formulas, not the figure's numbering typo.

## Possible-resource set

Eq. (14):

`BS_i = {p | EC(i,p) <= CTB_i and ET(i,p) <= CTD_i}`.

This test uses the task's execution time and execution cost, not EFT.

## Resource-selection rule

The paper defines three rules.

1. If `BS_i` is non-empty, choose the resource in `BS_i` minimizing Eq. (15):

   `alpha * EFT(i,p) + (1-alpha) * EC(i,p)`.

2. If `BS_i` is empty and `SWB_i >= 0`, choose from **all** resources using the same Eq. (15).

3. If `BS_i` is empty and `SWB_i < 0` **and** `SWD_i < 0`, choose the cheapest resource from all resources.

`alpha` is the user cost-time balance factor in `[0,1]`.

### Meaning of “cheapest resource”

The paper does not explicitly say whether Rule 3's phrase “cheapest resource” means the lowest advertised resource price rate `mu_p` or the lowest execution cost for the current task. The surrounding scheduling equations define and compare the current task's monetary burden through `EC(i,p) = mu_p * ET(i,p)`, and Eq. (14) also admits resources by `EC(i,p)`. The IFC adapter therefore interprets “cheapest resource” operationally as the resource with minimum **current-task execution cost `EC(i,p)`**, represented by `compute_cost_ncu[task][resource]`. This interpretation is explicit and tested; it is not silently presented as wording stated by the paper. Equal task costs are broken by smaller EFT and then `resource_id`.

### Underspecified branch in the paper

The three printed rules do not cover:

`BS_i == empty and SWB_i < 0 and SWD_i >= 0`.

This state is not proven unreachable by the equations. To make the implementation total and reproducible, the IFC adapter uses the **cheapest-resource fallback** when this uncovered state occurs. Rationale: the workflow is already below its expected budget trajectory, so the minimal completion of the published rule set is to prioritize cost recovery. This branch is recorded in `algorithm_internal_statistics` and is an explicit adaptation, not attributed to the paper.

## Cost-time normalization

**None is used in Eq. (15).** The paper directly combines EFT and execution cost. NSC and NSL, Eqs. (16) and (17), are evaluation/reporting metrics and are not used by the resource-selection formula.

For IFC, integer storage units are decoded to the benchmark's declared base units without normalization:

- `EFT_seconds = EFT_us / 1_000_000`,
- `EC_normalized_cost_units = EC_ncu / 1_000_000_000`.

With `alpha = a/d`, minimizing Eq. (15) is exactly equivalent to minimizing the integer numerator:

`a * EFT_us * 1000 + (d-a) * EC_ncu`.

The omitted denominator `d * 1_000_000_000` is common to every candidate. This preserves the paper's raw mixed score while avoiding binary floating point.

## Alpha parameter

- Paper definition: `alpha in [0,1]`.
- Paper illustrative example: `alpha = 0.5`.
- Paper experiments report variants `0.3`, `0.5`, and `0.7`.

The primary publication comparator is predeclared as **BDHEFT-0.5**, represented exactly as `1/2`; it is not selected after observing development results. The implementation may expose `3/10` and `7/10` as explicitly named sensitivity variants, but they must not silently replace the primary comparator.

## Constraint-repair rule

None. BDHEFT is a one-pass list heuristic; it does not iteratively repair a finished schedule.

## Tie-breaking

The paper does not specify ties for equal ranks, equal Eq. (15) scores, or equal cheapest costs. IFC deterministic adaptations are:

- equal rank / simultaneously ready: lexicographic `task_id`,
- equal Eq. (15) score: smaller EFT, then `resource_id`,
- equal cheapest task execution cost: smaller EFT, then `resource_id`.

These rules are deterministic only; they do not alter a strict paper preference.

## Termination / stopping condition

Terminate after all tasks in descending rank order have been considered.

## Population / iteration parameters

Not applicable. BDHEFT is deterministic and non-population-based.

## Original complexity claim

The paper states:

- rank computation: `O(n+e)`, approximated as `O(n^2)` for a dense DAG,
- scheduling: `O(n*m)`,
- with `m <= n`, overall `O(n^2)`.

The IFC adapter must not repeat `O(n^2)` unqualified: route-aware average communication for the HEFT rank examines heterogeneous resource routes, adding benchmark-specific work relative to the paper's approximately uniform-bandwidth model.

## Paper pseudocode / equations used

- Eqs. (1)–(3): execution time/cost and upward rank
- Eqs. (4)–(7): EST/EFT/makespan model
- Eqs. (8)–(13): SWB, SWD, BAF, DAF, CTB, CTD
- Eq. (14): possible-resource set
- Eq. (15): alpha cost-time resource score
- Fig. 2: one-pass BDHEFT pseudocode
- Eqs. (16)–(17): NSC/NSL are reporting only

## IFC adaptation mapping

| Original paper assumption | IFC treatment |
| --- | --- |
| Heterogeneous cloud resources | Use all materialized IoT, fog, and cloud execution slots as heterogeneous candidate resources |
| Every resource can execute every task | Current IFC v1 has a complete execution matrix and does not enforce task-memory eligibility |
| MIPS-derived task execution time | Use frozen `execution_time_us[task][resource]` |
| Linear execution price | Use frozen exact `compute_cost_ncu[task][resource]`; Dataset v1 already derives it from `price_ncu_per_second * execution_time` with exact ceiling |
| Approx. equal inter-resource bandwidth | Use frozen route-specific IFC communication through Dataset's network derivation; same-resource communication remains zero |
| Data-transfer monetary cost is zero | Matches IFC v1, which has no network monetary cost |
| No energy objective | Do not use energy in BDHEFT decisions; compute/network energy are post-decision benchmark metrics only |
| `avail(resource)` ready-time EFT model | Use append/ready-time availability inside BDHEFT's heuristic decision model; final benchmark schedule is rebuilt by the common insertion evaluator |
| Raw Eq. (15) time+cost score | Decode integer storage units to seconds and normalized cost units and compare exactly; do not introduce NSC/NSL normalization |
| Rule 3 “cheapest resource” is not formally disambiguated | Interpret as minimum current-task `EC(i,p)` / `compute_cost_ncu`; document and test the interpretation |
| Missing fallback for `SWB<0, SWD>=0, BS=empty` | Explicit cheapest-resource fallback, counted as an adaptation |
| Unspecified ties | Deterministic task/resource ID tie rules |
| Paper-specific deadline/budget generation for experiments | Not used; consume the benchmark's frozen public deadline and budget directly |

## Faithfulness classification

**MINOR IFC ADAPTATION**

The core BDHEFT priority, budget/deadline allocation equations, possible-resource test, Eq. (15) resource preference, and published fallbacks are preserved. Adaptations are required for route-specific IoT–Fog–Cloud communication, deterministic ties, interpretation of Rule 3's “cheapest” phrase, a genuinely missing paper branch, frozen integer unit representation, and the benchmark-wide authoritative insertion evaluator.

## Implementation gate

The implementation must not be labelled `EXACT`. Tests must cover:

1. Eqs. (8)–(13) using exact rational arithmetic,
2. Eq. (14) resource admissibility,
3. Eq. (15) exact unit-decoded score,
4. all three published selection rules,
5. Rule 3 cheapest-resource interpretation as minimum current-task execution cost,
6. the uncovered `SWB<0, SWD>=0` fallback,
7. deterministic tie behavior,
8. final rebuild through `generator.schedule`,
9. seed rejection for deterministic BDHEFT,
10. no energy term in the policy.
