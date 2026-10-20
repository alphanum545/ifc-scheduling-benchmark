# DB-ACO 2024 — paper-to-code audit

## Bibliographic identity

- **Algorithm:** DB-ACO — Deadline-Budget Constrained Ant Colony Optimization
- **Paper:** Siyuan Tao, Yuanqing Xia, Lingjuan Ye, Ce Yan, Runze Gao, *DB-ACO: A Deadline-Budget Constrained Ant Colony Optimization for Workflow Scheduling in Clouds*
- **Venue:** IEEE Transactions on Automation Science and Engineering, Vol. 21, No. 2
- **Current issue:** April 2024; originally published online 27 February 2023
- **DOI:** `10.1109/TASE.2023.3247973`
- **Primary source audited:** complete user-supplied IEEE paper PDF
- **Supplementary source checked:** authors' public repository `SiyuanTao/DBACO-workflow`; the repository exposes the experiment as a ZIP archive and a short README, so no unpublished implementation detail is treated as paper authority.

## Original optimization problem

DB-ACO minimizes total execution cost `TEC` under simultaneous workflow deadline and budget constraints:

`min TEC`

subject to:

`TET <= D` and `TEC <= B`.

The algorithm combines stochastic ACO task ordering with heuristic constraint distribution and service selection.

## Original cloud resource and monetary model

The paper assumes an **elastic cloud service model**, not a bounded fixed processor pool:

- the resource provider offers effectively "infinite" virtualized services;
- services belong to ordered types with different processing capabilities and prices;
- services are dynamically acquired and used by scheduling solutions;
- on-demand charging uses fixed billing intervals;
- partial billing intervals are rounded up;
- service cost is based on the lease start/finish span, Eq. (2):

  `EC_l = ceil((LFT_l - LST_l)/TI) * C_sl`;

- tasks assigned to the same service have zero communication time;
- all services are assumed in one physical area with common bandwidth and zero internal data-transfer monetary cost.

The paper's discussion explicitly attributes part of observed cost behavior to the number of service instances launched and to wasted fractions of paid charging intervals. Therefore these instance/billing semantics are part of the algorithm's experimental mechanism, not merely reporting details.

## Original task timing

Eq. (1):

`ET_i,l = w_i / p(s_l)`.

Eq. (3): inter-service transfer is `data_i,j/Bw`, while same-service transfer is zero.

Eq. (4):

`ST_i,l = max(RT_l, max_parent(FT_parent + TT_parent,i))`.

Eq. (5):

`FT_i,l = ST_i,l + ET_i,l`.

`RT_l` and the lease state therefore interact with service choice and monetary cost.

## Probabilistic upward rank and deadline distribution

The paper defines the fastest-service estimated execution time, Eq. (9):

`ET_i = w_i / p*`,

where `p*` is the processing capability of the highest service type.

Probabilistic upward rank, Eq. (10):

`pr_i = max_{j in succ(i)}(pr_j + gamma_j * TT_i,j) + ET_i`.

Eq. (11) stochastically decides whether transfer time is included. The paper uses a random draw and parameter `theta > 1`; experiments set `theta = 1.5` following the cited ProLiS/L-ACO work.

Sub-deadline, Eq. (12):

`SubD_i = D * (pr_entry - pr_i + ET_i) / pr_entry`.

Thus random rank construction also affects deadline distribution.

## Dynamic budget distribution

For the k-th task in an ant's current ordering, Eq. (13):

`TSB_k = B - sum_{i<k} cost(t_Ni) - sum_{j>=k} cost_min(t_Nj)`.

Eq. (14):

If `TSB_k >= 0`:

`CTB_k = cost_avg(t_Nk) + TSB_k * cost_avg(t_Nk) / sum_{i>=k} cost_avg(t_Ni)`.

Otherwise:

`CTB_k = cost_avg(t_Nk)`.

The values `cost`, `cost_min`, and `cost_avg` are evaluated under the paper's cloud service/lease-cost model. Therefore changing the cost model changes TSB, CTB, affordability, selected services, and later pheromone learning.

## Ant task ordering

Algorithm 2 uses Kahn's topological procedure. At every step an ant chooses one ready task according to Eq. (15):

`P(i->j) = tau_i,j^alpha * pr_j^beta / sum_ready(tau_i,j^alpha * pr_j^beta)`.

Paper experiment parameters:

- `alpha = 1`;
- `beta = 2`;
- `theta = 1.5`;
- colony size `colSize = 20`;
- maximum iterations `maxNo = 50`;
- pheromone evaporation `rho = 0.2`;
- relaxation-end iteration `kT = 35`;
- relaxation curve parameter `cp = 4`.

The paper initializes all pheromones at `tau_max` and says trail values are bounded by `tau_min` and `tau_max`. It states that these two bounds are set dynamically in the same way as L-ACO; it does not reproduce a self-contained formula for the dynamic bounds in DB-ACO.

## Service-selection rules

Affordable set, Eq. (16):

`S*_k = {s_l | c_k,l <= CTB_k}`.

Algorithm 3 defines four cases:

1. If `S*_k` is non-empty, select the cheapest affordable service that finishes before the current task sub-deadline.
2. If `S*_k` is empty and `TSB >= 0`, select the service with earliest finish time from all services.
3. If `S*_k` is empty and `TSB < 0`, select the cheapest service among services that finish before the sub-deadline.
4. If no service was selected by the first three cases, choose the earliest-finishing service.

Then a further mechanism is mandatory in Algorithm 3:

`while FT_k,j >= SubD_k and s_j is not the fastest:`

- **upgrade `s_j` to a faster service level**;
- recompute its cost and finish time.

This upgrade operation assumes ordered cloud service types and changes both processing capacity and unit price. Under the original lease-cost model it also changes the service-instance cost state.

## Relaxed epsilon comparison

The paper relaxes both budget and deadline during early ACO iterations. Eq. (17) gives relaxed budget:

For `0 <= k < kT`:

`B_e(k) = B + max(0, Cbase - B) * (1 - k/kT)^cp`.

For `k >= kT`:

`B_e(k) = B`.

It states that `D_e(k)` is calculated analogously using `Mbase` instead of `Cbase`.

However, the printed solution comparator Eq. (18) explicitly branches only on `D_e(k)` / `TET` and then chooses lower `TEC` where relevant. No branch in the printed comparator uses `B_e(k)`, even though the preceding prose states that both budget and deadline are relaxed. The paper therefore does not provide a self-contained operational role for `B_e(k)` in Eq. (18). This is recorded as a reproducibility ambiguity; it must not be silently repaired.

## Pheromone update

Eq. (19):

`tau_i,j(k+1) = (1-rho) * tau_i,j(k) + DeltaTau_i,j(k)`.

Eq. (20):

`DeltaTau_i,j(k) = 1/TEC_best(k)` for task-order edges visited by the iteration's local-best solution, otherwise zero.

Because reinforcement magnitude depends directly on `TEC_best`, changing the monetary model changes the ACO search trajectory itself.

## Stochasticity and repetition

The paper treats DB-ACO as stochastic and repeats stochastic approaches 10 times in its experiments. Any benchmark implementation would therefore need explicit externally supplied seeds and repeated runs. A faithful implementation must not hide RNG state.

## Original complexity claim

The paper derives:

`O(maxNo * colSize * n * (n + |T|))`,

where `|T|` is the number of service types. The service-upgrade loop is included in the analysis because a selected service may move through multiple ordered service types.

The scalability study reports DB-ACO runtime increasing faster than the compared methods and describes it as more suitable for offline than real-time scheduling.

## Frozen IFC v1 mismatch

The benchmark's frozen Dataset v1 intentionally exposes a different execution model:

- a finite materialized set of concrete IoT, fog, and cloud resource IDs;
- one serial slot per materialized resource;
- no operation to provision a fresh independent VM instance;
- no ordered "upgrade this service instance to the next faster VM type" operation;
- authoritative exact per-task `compute_cost_ncu[task][resource]`;
- no lease-start/lease-finish billing interval or rounded interval charge;
- route-specific heterogeneous IoT–Fog–Cloud communication rather than one common cloud bandwidth.

The common evaluator must remain identical across all competitors, so these semantics cannot be changed solely for DB-ACO.

## Why a fixed-pool DB-ACO rewrite would not be a faithful comparator

Replacing the original cloud model with fixed IFC slots would alter all of the following DB-ACO mechanisms simultaneously:

1. actual allocated-task `cost(t)` in Eq. (13);
2. `cost_min` and `cost_avg` in Eqs. (13)–(14);
3. total spare budget `TSB`;
4. current-task budget `CTB`;
5. affordable set `S*`;
6. cheapest-service comparisons;
7. service-upgrade behavior;
8. total execution cost `TEC` used in epsilon comparison;
9. `1/TEC_best` pheromone reinforcement;
10. the resulting stochastic search trajectory.

This is qualitatively different from adapting a communication formula or deterministic tie rule. It replaces the monetary/resource mechanism around which the published algorithm searches.

## Faithfulness classification

**NOT SUITABLE AS A PRIMARY FIXED-POOL IFC-V1 COMPARATOR**

No production `DBACO` scheduler is implemented in the primary benchmark registry.

This decision does **not** mean DB-ACO is a poor algorithm. It means that the published algorithm answers a materially different resource-allocation problem whose defining elastic-instance and billing semantics cannot be represented by the frozen common evaluator without invalidating cross-algorithm fairness.

## Optional future research use

If a later study introduces a separate elastic-IaaS benchmark with:

- VM type classes;
- dynamic instance creation;
- lease start/finish state;
- interval-rounded monetary billing;
- well-defined service-type upgrades;

then DB-ACO is an appropriate candidate for a faithful implementation there.

A separately named `DB-ACO-IFC` publication-inspired variant could also be explored in an ablation/sensitivity appendix, but it must be labelled **MAJOR MODEL ADAPTATION** and must not be presented as the original DB-ACO comparator.

## Audit gate outcome

- Full paper available: **yes**.
- Core equations/pseudocode available: **yes**.
- Primary paper parameters mostly available: **yes**.
- Self-contained pheromone-bound rule: **no**; referred to L-ACO.
- Self-contained use of relaxed budget in Eq. (18): **no / ambiguous**.
- Original resource/cost model representable by frozen IFC evaluator: **no**.
- Implement in primary fixed-pool registry: **no**.
