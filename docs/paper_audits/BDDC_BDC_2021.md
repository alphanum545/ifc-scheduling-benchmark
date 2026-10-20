# BDDC / BDC 2021 — paper-to-code audit

## Bibliographic identity

- **Algorithms:** Budget Deadline Delicate Cloud (BDDC) and Budget Deadline Cloud (BDC)
- **Paper:** Ahmad Taghinezhad-Niar, Saeid Pashazadeh, Javid Taheri, *Workflow scheduling of scientific workflows under simultaneous deadline and budget constraints*
- **Venue:** Cluster Computing
- **Year:** 2021
- **DOI:** `10.1007/s10586-021-03314-3`
- **Primary source audited:** complete user-supplied paper PDF

## Original scheduling problem

The paper schedules a scientific-workflow DAG in an elastic IaaS cloud under a demanded deadline `DD` and demanded budget `DB`. Both BDDC and BDC seek a schedule satisfying both constraints while offering different QoS preferences:

- **BDDC** is deliberately budget-conservative and aims for economical schedules and high utilization/success rate.
- **BDC** uses the entire remaining budget as the current task's sub-budget and is deliberately more time-aggressive, aiming for faster makespan and high success rate.

The paper evaluates success rate, cost ratio, time ratio, and resource utilization.

## Original infrastructure model

This assumption is central to the algorithms and is not a superficial simulation detail:

- Cloud providers expose a set of **resource types**.
- An arbitrary new instance of a resource type can be provisioned during scheduling.
- Existing provisioned instances and not-yet-provisioned resource types are evaluated separately in Algorithm 3.
- If the best Quality belongs to an existing instance, the task is placed there.
- If it belongs to a resource type, a **new instance** of that type is created and then receives the task.
- Pricing follows an IaaS time-interval model (one hour in the experiments).
- A task that finishes within an already paid billing interval can incur zero incremental task cost; extending an instance beyond its current billing cycle changes monetary cost.
- All instances are assumed to be in one region with a common bandwidth and zero data-transfer monetary cost.

This elastic provisioning / billing-cycle state is part of the resource-selection policy itself.

## Frozen IFC incompatibility

The frozen IFC v1 Dataset does **not** model elastic instance creation. It materializes a finite list of concrete resource slots. Each resource has:

- a fixed `resource_id`,
- one serial `concurrency_slots` slot,
- a fixed tier/class/MIPS/memory/power/price,
- authoritative per-task `compute_cost_ncu[task][resource]`.

The authoritative evaluator only accepts mappings to those materialized resource IDs. It cannot represent creating a second independent instance of the same resource class, nor does it charge by extending a shared instance billing cycle.

Therefore a paper-faithful BDDC/BDC implementation is impossible without changing the benchmark's resource and cost semantics. Changing those semantics is forbidden because all algorithms must share the same evaluator.

## Faithfulness decision

Both BDDC and BDC are classified as:

**MAJOR IFC ADAPTATION**

They remain useful as adapted publication-inspired comparators because their distinctive mechanisms — bottom-depth leveling, proportional deadline distribution, BDDC level-budget distribution, BDC remaining-budget behavior, EST-ready-task priority, and TQ/CQ Quality selection — can be preserved. However, results must be named `BDDC-IFC` / `BDC-IFC` (or equivalent) and must never be described as exact reproductions of the paper.

## Original workflow model

- DAG with precedence and data-transfer edges.
- Dummy zero-cost/time entry and exit tasks are added when needed.
- Makespan is exit-task finish time.
- Same-instance transfer time is zero; otherwise transfer time is data divided by bandwidth.

### Estimated completion quantity

Eq. (3):

`cpTime(t_i) = w_min(t_i) + max_{parent in pred(i)} TF(parent,i)`.

Here `w_min` is the fastest execution time of the task across resource types.

Eq. (4) recursively computes a static earliest-start quantity using the fastest-resource model:

- entry: `EST = 0`
- otherwise: maximum over parents of the parent's `EST + cpTime(parent)`.

The task-selection stage picks the ready task with minimum EST.

## Task leveling

The paper uses DBL bottom depth. Eq. (8):

- exit task has `BD=0`;
- otherwise `BD(t)=max_{child in succ(t)} BD(child)+1`.

Tasks with the same bottom depth form a level and have no precedence relationship within that level.

For IFC, dummy entry/exit nodes are treated implicitly rather than injected into the public Dataset instance. Multiple sinks behave as children of an implicit zero-time exit for bottom-depth purposes.

## Deadline distribution

Eq. (9):

`sigmaWeight = sum cpTime(t)`.

Eq. (10), for each level over currently unscheduled tasks:

`LW_k = sum_{t in level_k and UnSch} cpTime(t)`.

Eq. (11) gives cumulative level sub-deadlines:

`SDL_k = SDL_{k-1} + LW_k * DD / sigmaWeight`.

Levels are traversed from the entry side toward the exit side, so absolute sub-deadlines grow toward `DD`.

When Algorithm 3 obtains no non-negative Quality, the paper recomputes deadline distribution once using the unscheduled tasks and retries the current task once.

For IFC, all arithmetic is exact rational arithmetic. The redistribution uses the currently unscheduled task weights, as explicitly described by the paper's redistribution prose and Eq. (10).

## Budget distribution — BDDC

The prose and displayed Eq. (12) state a cumulative formula:

`SBL_k = SBL_{k-1} + LW_k * remainingBudget / sigmaWeight`.

However, **Algorithm 1 contradicts the displayed Eq. (12)**. It defines:

`sigmaBudget = remainingBudget / sigmaWeight`

and then, for every level:

`SBL_k = LW_k * sigmaBudget`.

Algorithm 1's non-cumulative form is a true partition of the remaining budget across levels; summing its level budgets returns the remaining budget. The cumulative printed Eq. (12) does not have that property and would give later levels accumulated budgets rather than a per-level sub-budget.

**Operational interpretation:** the IFC adaptation follows **Algorithm 1**, because it is the executable pseudocode for BudgetDistribution and is internally consistent with the concept of distributing remaining budget across levels. The audit records the printed Eq. (12) conflict; it is not silently corrected.

`remainingBudget` is demanded budget minus cost already consumed.

When Algorithm 3 retries after all Quality values are negative, BDDC recomputes both deadline and budget distributions once over the unscheduled remainder.

## Budget handling — BDC

BDC does not use BudgetDistribution. The paper states that the task sub-budget is derived from the **entire remaining budget** at each scheduling cycle.

Thus the distinguishing mechanism is preserved in IFC:

- BDDC: current level gets a proportional slice of remaining budget.
- BDC: current task sees the entire remaining budget.

On the one allowed retry, BDC recomputes deadline distribution only; there is no BDDC-style budget redistribution.

## Task selection

Algorithm 2:

1. start with children of the dummy entry task;
2. while ready queue is non-empty, select `minEST(Q)`;
3. provision/assign that task;
4. add children whose parents are now all scheduled.

The paper does not specify ties. IFC adaptation: equal EST is broken lexicographically by `task_id`.

## Original cost model

The paper uses cloud billing intervals. Eq. (5) defines an instance billing cycle from its finish time and charging interval. Eq. (6) makes the current task's monetary cost depend on whether assigning it extends the instance beyond already paid intervals. Consequently an existing instance may be economically different from provisioning a new instance of the same type.

This cannot be reproduced by the frozen evaluator without changing cross-algorithm cost semantics.

### IFC cost adaptation

Use authoritative frozen `compute_cost_ncu[task][resource]` as the task cost for every candidate resource. This intentionally removes elastic billing-cycle reuse and is the principal reason for the `MAJOR IFC ADAPTATION` classification.

`remainingBudget` is maintained from those same authoritative per-task costs so algorithm-internal constraint reasoning uses the same monetary semantics that the common evaluator will report.

## Original candidate resource model

Algorithm 3 evaluates:

1. all already provisioned instances, then
2. every resource type as a possible new instance.

If a resource-type candidate wins, a new instance of that type is created.

### IFC resource adaptation

Every materialized IFC resource slot is evaluated exactly once as a candidate execution resource. No synthetic resource IDs are created and no duplicate instance of a class is invented. This removes the paper's existing-instance-versus-new-instance distinction, another major adaptation required for evaluator compatibility.

Candidate finish times use the pinned Dataset insertion candidate primitive so all competitors retain the benchmark's authoritative precedence, serial-slot, and route-specific communication semantics.

## Time Quality, Cost Quality, and final Quality

The displayed paper formulas are authoritative.

Eq. (13):

`TQ(t_i,r) = (SDL_k - FT(t_i,r) - FT_min(t_i)) / SDL_k`.

Eq. (14):

`CQ(t_i,r) = (SBL_k - TC(t_i,r) - TC_min(t_i)) / SBL_k`.

Eq. (15):

`Quality(t_i,r) = omega*TQ(t_i,r) + (1-omega)*CQ(t_i,r)`.

### Paper prose inconsistency

The prose says TQ/CQ become negative when time/cost exceeds the sub-deadline/sub-budget. The displayed equations actually become negative when:

- `FT + FT_min > SDL`, or
- `TC + TC_min > SBL`,

which can happen before the candidate alone exceeds its limit. The IFC adaptation preserves the **displayed equations**, not the looser prose statement.

For BDC, `SBL` in CQ is the current `remainingBudget`.

## Weight parameter

The paper denotes the Eq. (15) weight by `omega` (the prose also calls it `x`). `omega` close to 1 gives more deadline/time importance; lower `omega` gives more cost importance.

The paper's Figure 11 performs a sensitivity sweep from `0.1` through `0.9`; the plotted mean success rate is highest around `0.5`. The text does not explicitly identify one value as the default used for all main comparison figures.

To prevent any tuning on our 160 development instances, the primary IFC adaptations are preregistered at:

`omega = 0.5 = 1/2` exactly.

This is a neutral benchmark setting informed by the paper's own reported sensitivity study, **not claimed as a paper-specified default**. No alternative omega may replace it after development results are observed. Sensitivity variants, if ever reported, must be named separately.

## Candidate minimum values

`FT_min(t)` is the minimum candidate finish time across the candidate resources; `TC_min(t)` is the minimum current-task cost across candidates. Under IFC both are calculated over all materialized resource slots using the same candidate-time and per-task-cost semantics used by the adapted policy.

## Negative-Quality retry

Algorithm 3 permits exactly one retry for the current task when the maximum candidate Quality is negative:

- BDDC: recompute deadline and budget distribution for the unscheduled remainder;
- BDC: recompute deadline distribution only.

After the one retry, even a negative maximum is accepted and its best candidate is assigned.

The paper does not specify tie-breaking among equal Quality values. IFC deterministic tie rule:

1. higher Quality;
2. smaller candidate finish time;
3. lower authoritative task cost;
4. lexicographic `resource_id`.

## Communication model

Original: common intra-region bandwidth; same-instance communication zero.

IFC adaptation:

- static `cpTime` uses a route-aware average communication value derived from the pinned Dataset primitives because one global cloud bandwidth does not exist in IoT–Fog–Cloud;
- candidate finish time uses exact route-specific communication from the pinned Dataset candidate primitive;
- same-resource communication remains zero;
- no network monetary cost is introduced.

This network change is substantial but still subordinate to the larger provisioning/cost-model mismatch.

## Energy model

The 2021 BDDC/BDC policy has no energy objective. IFC compute and network energy are evaluated after the decision only and must not affect candidate Quality.

## Constraint feasibility

The paper measures a schedule as successful if both actual final cost and makespan satisfy DB/DD. BDDC/BDC do not prove that every mapping will satisfy both constraints; the trade-off and redistribution heuristics aim to improve the success rate.

The IFC common evaluator independently decides deadline, budget, and joint feasibility. Algorithm-internal Quality or budget calculations are diagnostic only.

## Termination

Both algorithms terminate after every real workflow task is assigned. No finished-schedule repair or backtracking phase is described.

## Population / iteration parameters

Not applicable. Both are deterministic heuristics once `omega` and deterministic tie rules are fixed.

## Original complexity claim

The paper claims both algorithms have overall `O(n^2)` complexity under its assumptions, with the instance-provisioning stage `O(n*m)` and at most one redistribution attempt per task. It reports redistribution occurred for about 1% of tasks in its experiments.

The IFC adaptation must report this as the **paper's original claim** rather than assert it unqualified, because route-aware communication and the fixed heterogeneous candidate pool alter constant factors and some primitive costs.

## Paper pseudocode / equations used

- Eqs. (1)–(7): cloud scheduling/cost/problem model
- Eq. (8): bottom-depth leveling
- Eqs. (9)–(11): workflow/level weights and cumulative sub-deadline
- Eq. (12) plus Algorithm 1: BDDC budget distribution (with documented inconsistency)
- Algorithm 2: min-EST ready-task selection
- Eqs. (13)–(15): TQ, CQ, Quality
- Algorithm 3: existing-instance/resource-type comparison and one retry
- Algorithm 4: BDDC top-level flow; BDC differs by omitting BudgetDistribution and using remaining budget

The paper's own DB/DD generation Eqs. (18)–(19) are not used; the frozen benchmark's public constraints are consumed directly.

## IFC adaptation mapping

| Original paper assumption | IFC treatment |
| --- | --- |
| Elastic IaaS resource types, unlimited/new instances | **Major change:** evaluate only the finite materialized IFC resource slots |
| Existing instance can be cheaper due to already paid billing cycle | **Major change:** use authoritative per-task `compute_cost_ncu` for every mapping |
| Hourly billing-cycle monetary model | **Major change:** removed from policy so internal cost matches common evaluator semantics |
| Uniform same-region bandwidth | Route-aware IFC average communication for static weights; exact route communication for candidate FT |
| Same-instance communication zero | Preserved |
| DBL bottom-depth leveling | Preserved, with implicit dummy entry/exit |
| Proportional deadline distribution | Preserved with exact rational arithmetic |
| BDDC level budget distribution | Preserve Algorithm 1 non-cumulative partition and record Eq. (12) inconsistency |
| BDC current sub-budget = remaining budget | Preserved |
| Ready task with minimum EST | Preserved; deterministic task-id tie |
| TQ/CQ/Quality formulas | Preserved exactly as printed |
| `omega` user preference | Primary adaptation fixed a priori at exact `1/2`; not claimed as paper default |
| One negative-Quality redistribution/retry | Preserved |
| No energy objective | Preserved; energy measured only after decision |
| Paper-specific constraint generation | Not used; frozen benchmark DB/DD consumed directly |

## Comparator inclusion decision

Include **both** adapted variants because the paper deliberately defines two different scheduling behaviors and the distinction is scientifically useful:

- `BDDC-IFC-0.5`: cost-conservative level-budget distribution;
- `BDC-IFC-0.5`: time-aggressive use of entire remaining budget.

Neither may be referred to as an exact paper reproduction. Publication tables should include the faithfulness label `MAJOR IFC ADAPTATION` or equivalent methodological disclosure.

## Implementation gate

Tests must cover:

1. bottom-depth levels and min-EST ready-task ordering;
2. `cpTime`, workflow weight, and level weights;
3. cumulative Eq. (11) sub-deadlines;
4. BDDC Algorithm-1 level-budget partition and the documented Eq. (12) conflict;
5. BDC remaining-budget sub-budget behavior;
6. exact Eqs. (13)–(15) with `omega=1/2`;
7. one negative-Quality redistribution only;
8. deterministic tie behavior and seed rejection;
9. no energy term in either policy;
10. use of fixed IFC resource slots only — no invented duplicate instance IDs;
11. final authoritative evaluation outside algorithm runtime;
12. explicit `MAJOR_IFC_ADAPTATION` internal metadata.
