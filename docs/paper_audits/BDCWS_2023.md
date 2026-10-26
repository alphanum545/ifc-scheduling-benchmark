# BDCWS 2023 — paper-to-code audit

## Bibliographic identity

- N. Zhou, W. Lin, W. Feng, F. Shi, X. Pang, "Budget-deadline constrained approach for scientific workflows
  scheduling in a cloud environment", *Cluster Computing* 26(3):1737–1751 (online 8 Sep 2020; issue 2023).
- DOI 10.1007/s10586-020-03176-1. Audited from the full-text PDF supplied by the author (2026-10-26).
- Algorithm name: Budget-Deadline Constrained Workflow Scheduling (BDCWS). Section 4.2 is headed "The MW-HBDCS
  algorithm" in the PDF, but the text and Table 2 both describe BDCWS. This is an editorial slip.

## Original scheduling problem

Single DAG workflow, a user deadline DEADLINE and a user budget BUDGET. A schedule is successful when the
makespan is at most DEADLINE and the cost at most BUDGET (Section 3.2). Static, one pass, deterministic.

## Original infrastructure model

- Elastic IaaS cloud with 9 VM types (Table 3).
- A VM is leased per billing period IT, with a boot time of 97 s and a billing period of 1 s.
- R is the set of VMs already in use; R' holds one temporary new VM of each type.
- Bandwidth is a single 20 Mbps between VMs, with zero transfer on the same VM and no data-transfer cost.

## Frozen IFC incompatibility

The same incompatibility as BDDC/BDC (see `BDDC_BDC_2021.md`) applies. The frozen IFC v1 model has:
- a fixed list of materialized resources, each with one serial slot;
- authoritative per-task `compute_cost_ncu`;
- no instance creation, boot time or billing-period reuse;
- route-specific communication.

## Faithfulness decision

**MAJOR IFC ADAPTATION**, for the same reasons as BDDC/BDC. Name in results: `BDCWS-IFC`. The distinctive
mechanisms are preserved:
1. upward rank with minimum execution time;
2. TOD;
3. TOAB with the optimistic spare budget, which reserves the cheapest cost of every unassigned task;
4. the affordable set;
5. the three-way selection rule;
6. the bi-factor BF = TF + CF.

## Task priority rule (Eq. 13, Table 2 line 3)

`urank_i = ET_i^min + max_{child} (urank_child + TT_{i,child})`, with `urank_exit = ET_exit^min`.
- **IFC:** `ET^min` is the minimum `execution_time_us` over all resources. `TT` is the Dataset's average
  communication time of the edge, the same quantity HEFT/DBCS use, because IFC transfer time is route-specific
  rather than one bandwidth.
- Line 3, "the next ready task with highest urank value", is implemented with the pinned
  `_priority_order` (ready-list heap, ties by task ID).

## Deadline handling (Eqs. 14–15)

`OSD = DEADLINE − ST^best − urank` and `TOD = ST^best + OSD + ET^min = DEADLINE − urank + ET^min`.
- `ST^best` is the start time on the resource with the earliest finish time (Definition 11). It is computed
  over all IFC resources, with ties broken by finish, then cost, then resource ID.
- `ST^best` cancels in TOD, so TOD is a latest-finish bound from the minimum-time rank. The implementation
  evaluates both equations as printed.

## Budget handling (Eqs. 16–17)

- `OSB = BUDGET − Σ_{assigned} cost − Σ_{unassigned} cost^min`. The unassigned set includes the current task
  (`T − T_assigned`), so this is a DBCS-type cheapest-remaining reserve and **deadline-blind**.
- `TOAB = ET^max / IT · VMC(vmt(vm_max)) + OSB`: the task's cost on the slowest VM type, plus OSB.
  - **IFC:** the per-task cost `compute_cost_ncu[t][r_max]`, where `r_max` is the resource with the largest
    `execution_time_us` for the task. Ties go to the lower cost, then the lower resource ID.
- Affordable set (Eqs. 18–19): resources with `cost ≤ TOAB`.
  - **IFC:** R ∪ R' becomes the full materialized resource list, so S_affordable ∪ S'_affordable is one set
    over all resources. Line 7 tests whether that set is empty.

## Resource-selection rule (Section 4.2.2, Table 2 lines 7–31)

1. Affordable set empty and `TOD ≤ 0`: the earliest-finish resource (ties: cost, ID).
2. Affordable set empty and `TOD > 0`: the cheapest resource (ties: finish, ID).
3. Otherwise, among affordable resources with `FT < TOD`:
   - (a) if any exist, pick the smallest BF (ties: finish, cost, ID);
   - (b) otherwise, the earliest-finish affordable resource.

`BF = TF + CF`, `TF = FT / ((ET^vm / urank) · OSD)` (Eq. 21) and `CF = cost / OSB` (Eq. 22).

## Undefined normalization cases

- **TF with OSD ≤ 0.** Unreachable inside branch (a). If OSD ≤ 0, then
  `FT ≥ FT^best ≥ ST^best + ET^min ≥ DEADLINE − urank + ET^min = TOD` for every resource, so no resource has
  `FT < TOD` and branch (a) is empty. The implementation asserts this.
- **CF with OSB ≤ 0.** Possible, because TOAB can still admit a resource when the slowest-VM cost exceeds the
  cheapest cost. The paper does not define it. A negative OSB would reverse the cost preference (dearer would
  look better), and OSB = 0 divides by zero.
  - **Rule adopted:** when `OSB ≤ 0`, CF uses a denominator of 1 ncu, the smallest positive budget unit. This
    keeps the paper's monotonicity (cheaper gives a lower CF) and makes cost dominate when no spare budget is
    left, which matches the intent of Eq. 22.
  - The count of such placements is reported in `internal_statistics` (`osb_nonpositive_bf_count`).
- **urank = 0** (zero-time tasks): ET^vm / urank is undefined. The IFC v1 data has positive execution times on
  every resource, so the implementation asserts urank > 0.

## Constraint guarantees

- **Budget: not hard.** Rule 1 picks the earliest-finish resource regardless of cost.
- **Deadline: not guaranteed.**
- There is no precondition check: the paper does not reject B < Σ cost^min.

## Cost, communication and energy model

- Cost: authoritative per-task `compute_cost_ncu`. The paper's billing periods are removed, as for BDDC/BDC.
- Communication: the pinned `_candidate_assignment` gives route-specific transfer times and insertion-based
  start times. This is the same primitive used by every comparator.
- Energy: not used by the policy; the evaluator reports it afterwards.

## Termination; parameters; complexity

- One pass over the tasks. There are no tunable parameters: BDCWS has no weight.
- Paper complexity O(n²·m). The IFC implementation evaluates every resource for each task:
  O(n·m) candidate evaluations plus the ranking.

## IFC adaptation mapping (summary)

| Paper element | IFC implementation | Change |
|---|---|---|
| R ∪ R' (used and new VMs) | all materialized resources | major (shared with BDDC/BDC) |
| Billing-period cost, boot time | per-task `compute_cost_ncu`, no boot | major (shared) |
| TT = data/bw | Dataset average communication (rank), route-specific (timing) | minor |
| TOAB slowest-VM-type cost | cost on the resource with the largest execution time | minor |
| CF with OSB ≤ 0 | denominator 1 ncu | undefined-case rule |

## Comparator inclusion decision

**Include.** BDCWS is the newest dedicated joint deadline–budget list heuristic found by the 2026-10-26
literature audit (`IFC-Research-Paper/notes/LITERATURE_AUDIT_2022_2026.md`). It reports +26.3–79.7% success over
DBWS and BDAS. It also tests the paper's claim directly: it uses DBCS's deadline-blind reserve together with a
deadline-aware scoring rule.

## Implementation gate

The implementation is `algorithms/bdcws/scheduler.py`, with tests in `tests/historical/test_bdcws.py`:
- a hand-computed single-task case for every branch;
- the OSB ≤ 0 rule;
- determinism;
- a check that every decision is a complete, topological mapping.
