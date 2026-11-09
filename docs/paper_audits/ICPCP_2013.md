# IC-PCP 2013 — paper-to-code audit (paper 2 comparator)

## Bibliographic identity

- **Algorithm:** IC-PCP — IaaS Cloud Partial Critical Paths (the one-phase algorithm; IC-PCPD2 is not ported)
- **Paper:** Saeid Abrishami, Mahmoud Naghibzadeh, Dick H.J. Epema, *Deadline-constrained workflow scheduling
  algorithms for Infrastructure as a Service Clouds*
- **Venue:** Future Generation Computer Systems 29(1), 158–169, 2013
- **DOI:** `10.1016/j.future.2012.05.004`
- **Primary source audited:** complete user-supplied PDF (12 pages)

## Original problem

Minimize workflow execution cost subject to a user deadline. No budget. Same problem as paper 2.

## Original resource and monetary model

- IaaS provider with several computation services (types); any number of instances of each can be launched.
- Pay-per-interval billing: partial intervals are charged in full. The cost of placing a path on an existing
  instance is the cost of the *new* intervals it adds; leftover time in a paid interval is free.
- Transfer time `TT(e_ij)` depends only on the data size, and is 0 when both tasks run on the same instance.
- An instance runs one task at a time.

## Algorithm (as published)

1. Add dummy `t_entry` and `t_exit`. Compute EST, EFT (Eqs. 1–2) with the minimum execution time `MET` over
   services, and LFT (Eq. 3) backward from `LFT(t_exit) = D`. Set `AST(t_exit) = D` (Algorithm 1).
2. **Critical parent** of `t_i`: its unassigned parent with the latest data arrival `EFT(t_p) + TT(e_p,i)`.
3. **Partial critical path** of `t_i`: follow critical parents back until a task with no unassigned parent.
4. **AssignParents(t)** (Algorithm 2): while `t` has an unassigned parent, build its PCP, call AssignPath,
   update EST/EFT of successors and LFT of predecessors, then call AssignParents recursively on each path
   task, from the start of the path to its end.
5. **AssignPath(P)** (Algorithm 3): put the whole path on the cheapest *applicable existing instance*. An
   instance is applicable if every path task finishes by its LFT and the path uses that instance's extra
   time. Two placement cases: right before a child of the path's last task, shifting that child and its
   successors forward; otherwise before the instance's first task or after its last. If no instance is
   applicable, launch a new instance of the cheapest service that finishes every path task by its LFT.
6. Deterministic. Complexity `O(n²)` (paper's claim).

## Mismatch with the frozen IFC v1 model, and decisions

| Paper mechanism | IFC v1 | Decision |
| --- | --- | --- |
| Launch any number of instances | Fixed materialized resources | Every resource is an "existing instance"; nothing is launched |
| Interval billing; leftover time free (applicability condition ii) | Exact per-task `compute_cost_ncu` | Path cost = Σ `c_ir`; condition ii is dropped (it only concerns billing) |
| New instance of the cheapest service meeting all LFTs (always possible on the elastic model when D ≥ the MET critical path) | No new instances | If no resource is applicable: the resource minimizing the largest LFT overrun, ties by cost, then resource id. Counted as `fallback_paths` |
| Placement before the instance's first task or after its last; or before a child, shifting it and its successors | Insertion into idle gaps; committed tasks are not moved | Path tasks are placed consecutively in path order, each in the earliest idle gap after its ready time. Shifting committed tasks is not represented |
| `TT(e_ij)` from data size only | Route-specific tiered communication | Exact route time when both endpoints are placed (0 on the same resource); otherwise the pinned route-aware average (`_upward_ranks`), as in the other ports |
| `MET(t_i)` | Per-resource execution times | `min_r p_ir` |
| Dummy `t_exit` with `AST = D` | — | Real sinks get `LFT = D`; the exit's partial critical path starts at the unassigned sink with the latest EFT; repeated until every task is assigned (equivalent to AssignParents(t_exit)) |
| Schedule = (instance, AST) per task | Evaluator rebuilds from (task order, resource map) | Order = topological, earliest internal start first; the authoritative evaluator recomputes the times |

## Faithfulness classification

**MAJOR MODEL ADAPTATION**, the same class as ProLiS and the companion paper's BDC/BDDC.

Preserved: the problem, EST/EFT/LFT, the critical parent and partial critical paths, the recursive
AssignParents order, and the defining rule of AssignPath (a whole path on one resource, the cheapest one
meeting every LFT).

Lost: the elastic launch, interval-packing incentives, and shifting committed tasks.

Because the evaluator rebuilds the schedule from the order and the mapping, the internal plan can meet D while
the rebuilt one misses it. This is reported, not repaired.

## Observed behaviour (dev, 9 November 2026)

IC-PCP places each path at its earliest start. When a child path is placed early, the parents assigned after
it inherit little slack and are pushed onto fast, priced resources. On relaxed deadlines this gives costs far
above the reference. Example: dev CyberShake 60, relaxed: 24 of 60 tasks on `cloud-002`, cost 10.9× `C_ref`,
internal makespan 0.18·D. This follows from the published as-early-as-possible placement, which the port keeps.
