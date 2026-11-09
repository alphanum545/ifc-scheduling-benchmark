# ProLiS 2017 — paper-to-code audit (paper 2 comparator)

## Bibliographic identity

- **Algorithm:** ProLiS — Deadline-constrained Probabilistic List Scheduling (and L-ACO, same paper)
- **Paper:** Quanwang Wu, Fuyuki Ishikawa, Qingsheng Zhu, Yunni Xia, Junhao Wen, *Deadline-Constrained Cost
  Optimization Approaches for Workflow Scheduling in Clouds*
- **Venue:** IEEE Transactions on Parallel and Distributed Systems 28(12), 3401–3412, December 2017
- **DOI:** `10.1109/TPDS.2017.2735400`
- **Primary source audited:** complete user-supplied accepted-manuscript PDF (12 pages). The authors' public
  code (`github.com/wuquanwang/workflow`) is referenced in the paper but not used as authority.

## Original optimization problem

Exactly the paper-2 problem (Eq. 8):

`min f(R, M)  s.t.  makespan(R, M) <= D`

where `f` is total execution cost. No budget. This is the closest problem match among all audited methods.

## Original resource and monetary model

- "Infinite" IaaS services of 9 types (speed 1.0–5.0, cost 0.12–1.0 per interval); any number of instances.
- On-demand interval billing, Eq. (2): `EC_l = ceil((LFT_l − LST_l)/TI) × c(s_l)`, TI = 1 hour; lease period
  per Eqs. (14)–(15) includes incoming and outgoing transfer time.
- One common bandwidth, free internal transfer; same-service transfer time 0 (Eq. 3).
- Start time `ST = max(RT_l, max over parents (FT + TT))` (Eq. 4): append at the service's ready time, no
  insertion into idle gaps.

## Algorithm (as published)

1. **Upward rank** with the fastest service `s*` (Eq. 9).
2. **Probabilistic upward rank** (Eqs. 11–12): the transfer term to child `t_j` is counted only with probability
   depending on `ccr_j = (w_j/p(s*)) / (data_ij/bw)` and `θ`; `θ = 1.5` (Table III).
3. **Sub-deadline** `psd_i = D × (pr_entry − pr_i + w_i/p(s*)) / pr_entry` (Eq. 13).
4. **Order** tasks by non-increasing `pr_i`.
5. **Service selection** (Algorithm 1): candidates = services already used plus one new instance per type;
   pick the one that meets `psd_i` with the minimum **cost increment** (lease cost after minus before adding the
   task). If none meets it: the service with the earliest finish time, then upgrade that service's type step by
   step while `psd_i` is still missed, updating the finish times of all tasks on it.
6. Stochastic through `rand()` in Eq. (12); the paper reports the average of 10 runs.

L-ACO (Algorithm 2) replaces step 4 with ant-built topological orders (MMAS pheromone, Table II parameters,
ε-relaxed deadline Eqs. 17–18) and reuses steps 1–3 and 5.

## Mismatch with the frozen IFC v1 model

| Paper mechanism | IFC v1 | Decision |
| --- | --- | --- |
| Elastic instances, "new service per type" | Fixed materialized resources | Candidates = all resources (each always available) |
| Interval billing, cost increment | Exact per-task `compute_cost_ncu[task][resource]` | Cost increment = `c_ir` (no lease packing) |
| Type upgrade loop (Alg. 1 lines 6–9) | Resources cannot change type | Dropped; fallback is earliest finish only |
| One bandwidth `bw` for rank and `ccr` | Route-specific tiered communication | Route-aware average communication from the pinned Dataset primitive (`_upward_ranks`), as in the companion paper's BDC/BDDC ports |
| `w_i / p(s*)` | Per-resource execution times | `min_r p_ir` (fastest resource for that task) |
| Append-only start time (Eq. 4) | Evaluator uses insertion into idle gaps | Candidate finish times from the pinned insertion primitive (`_candidate_assignment`), so every comparator sees the authoritative timing |
| `rand()` | Benchmark needs reproducibility | Seeded PRNG; 10 seeds per instance, report mean and best (paper reports mean) |

## Faithfulness classification

**MAJOR MODEL ADAPTATION**, same class as the companion paper's BDC/BDDC.

Preserved: the problem, probabilistic upward rank, deadline distribution, ordering, and the selection rule
"cheapest resource that meets the sub-deadline, else earliest finish".

Lost: interval-packing incentives and instance upgrades. These are the parts most tied to elastic IaaS, and
they cannot be represented by the common evaluator.

Unlike DB-ACO (rejected by the companion audit), the defining mechanism here — deadline distribution plus
cheapest-meeting-sub-deadline selection — survives intact on a fixed pool.

## L-ACO

Implementable on top of the ProLiS port (ordering only changes). Two gaps:
- the pheromone bounds `τmin`, `τmax` are referred to MMAS [38] rather than defined in the paper;
- `M_base` in Eq. (17) is "all tasks on the slowest service"; the IFC analogue is all tasks on the slowest resource.

Treat it as optional and implement it only after ProLiS.

## Complexity (paper claim)

`O(n·(n + |T|))` for ProLiS. With a fixed pool of `m` resources and insertion search, the IFC port is
`O(n·m·k)`, where `k` is the number of intervals on a resource.
