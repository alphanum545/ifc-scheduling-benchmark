# PSO-SA 2024 — paper-to-code audit

## Bibliographic identity

- **Method:** hybrid improved Particle Swarm Optimization + Simulated Annealing (PSO-SA)
- **Paper:** Navid Khaledian, Keyhan Khamforoosh, Reza Akraminejad, Laith Abualigah, Danial Javaheri, *An energy-efficient and deadline-aware workflow scheduling algorithm in the fog and cloud environment*
- **Venue:** Computing 106 (2024), 109–137
- **DOI:** `10.1007/s00607-023-01215-4`
- **Published online:** 26 August 2023
- **Primary source audited:** complete user-supplied paper PDF

## Original problem

The paper considers IoT applications as workflows of interdependent tasks and schedules them in a heterogeneous fog/cloud setting. Its stated goals are to:

- reduce total energy consumption;
- reduce makespan / task finish time;
- satisfy task deadlines where possible;
- minimize deadline violation when deadlines cannot all be satisfied;
- respect per-task priority so higher-priority deadline violations are penalized more strongly.

The method is explicitly a two-stage hybrid metaheuristic:

- improved PSO generates/prioritizes task-resource assignments;
- SA is invoked around improved global-best solutions to reduce deadline violation while not increasing energy.

## Constraint mismatch with the fixed research benchmark

The paper does **not** formulate or enforce a user monetary budget constraint.

Although introductory motivation mentions service cost and company expense, the actual optimization model and algorithm use energy, response/deadline quantities, task priority, and makespan. No analogue of the benchmark's public workflow-level `budget_ncu` participates in PSO-SA's fitness or feasibility decision.

The frozen research problem is specifically **joint deadline + monetary budget constrained workflow scheduling**. Adding a budget term or budget-repair mechanism to PSO-SA would create a new hybrid rather than reproduce the published method.

## Architecture

The paper presents a three-layer architecture:

1. IoT devices generate requests/workflows;
2. fog nodes provide nearby heterogeneous computation and are managed by a fog controller / fog-breaker;
3. cloud data centers provide powerful remote computation/storage.

The paper's mathematical allocation model is written over a set of heterogeneous processing nodes `N={N1,...,Nm}`, with the decision variable `x_ik` indicating that task `k` is assigned to node `i`. Much of the explicit energy model is described in terms of fog nodes.

The IoT devices are request/data sources rather than execution candidates in the formulation. Therefore the paper does not directly model the benchmark's symmetric possibility of executing a workflow task on a materialized IoT execution resource.

## Task inputs required by the paper

Each task includes paper-specific attributes such as:

- task size;
- **per-task deadline**;
- **per-task priority**;
- input file size;
- output file size;
- parent/dependency information.

The frozen IFC benchmark exposes a workflow DAG plus a **single workflow-level deadline and budget**. It does not provide independently calibrated per-task deadlines or task-priority labels.

Inventing per-task deadlines/priorities from the workflow-level deadline would materially add an allocation policy not present in the dataset and could leak/tune extra structure. Therefore these required PSO-SA inputs are not available under the benchmark contract.

## Network and response-time model

The paper models each processing-node link with bandwidth and propagation delay. Task response time includes:

- propagation delay;
- input/output transfer time;
- execution time;
- waiting time behind earlier tasks assigned to the same processing node.

Nodes process one task at a time and tasks are non-preemptive.

This is conceptually compatible with serial heterogeneous workflow scheduling, but the exact response-time model differs from Dataset-v1's route-specific dependency communication and insertion scheduling.

## Energy model

For each processing node the paper computes:

- active time from the execution durations of tasks allocated to the node;
- global makespan as maximum node active time;
- idle time as makespan minus active time;
- energy as active-time * active-power + idle-time * idle-power.

Total system energy is the sum across nodes.

This differs materially from the frozen benchmark's primary compute-energy semantics, which charge task compute energy and explicitly do **not** add system-wide idle energy. Network energy is separately evaluated by Dataset-v1.

Changing Dataset energy semantics for PSO-SA alone would violate the common-evaluator requirement. Conversely, replacing the paper energy objective with Dataset task-only energy would change the fitness landscape driving both PSO and SA.

## Deadline / priority objective

The paper defines task response time and a binary deadline-satisfaction indicator. Deadline violation for task `k` is proportional to:

`max(0, response_time_k - task_deadline_k) * task_priority_k`.

Total priority-weighted violation is summed across tasks.

The optimization objective combines total energy consumption and this priority-aware total deadline violation with weights that the paper states are changed dynamically during simulation.

Thus deadline handling is **per task**, not a single final-workflow makespan constraint as in the current benchmark.

## Improved PSO representation

A particle is an `m x n` real-valued matrix, with rows corresponding to processing nodes/VMs and columns corresponding to tasks.

For each allowed task, the task is assigned to the row/node with the maximum particle value in its column. Among currently precedence-allowed tasks, the paper chooses the task with the greatest such maximum value, producing both a task order and resource mapping while respecting workflow dependencies.

The paper uses matrices:

- `x` for task-to-node allocation;
- `y` for routes (formed using Dijkstra's algorithm);
- `z` for task priority/order relationships.

Improved PSO changes velocity coefficients from fixed constants to dynamically derived probabilities for retaining current motion, moving toward personal best, and moving toward global best.

## SA stage

Whenever the PSO global optimum changes, SA generates neighboring candidate solutions from the current global best.

The paper's described acceptance logic favors a candidate when priority-weighted deadline violation decreases without increasing total energy; a probabilistic SA acceptance path permits some otherwise non-improving candidates to escape local optima. Temperature is reduced and inner/outer SA stopping conditions control termination.

## Published experimental parameters

The paper reports experimentally selected settings:

- PSO iterations: `1000`;
- population / particles: `200`;
- internal SA iterations: `15`;
- temperature reduction factor: `0.99`;
- initial temperature: `0.025`;
- stochastic experiments replicated `20` times and means reported.

Any reproduction would therefore need explicit externally controlled seeds and repeated runs.

## Evaluation criteria

The paper evaluates:

- total energy consumption;
- makespan;
- total deadline violation time;
- deadline satisfaction percentage;
- priority-aware deadline satisfaction percentage.

Monetary budget feasibility is not an evaluation criterion of the proposed method.

## Frozen IFC-v1 incompatibilities

A direct implementation in the primary comparator set would require inventing or changing at least four central semantics:

1. **budget:** PSO-SA has no monetary budget constraint, while the target problem requires one;
2. **deadlines:** PSO-SA requires per-task deadlines, while the benchmark supplies one workflow-level deadline;
3. **priority:** PSO-SA requires per-task priority values, which the benchmark does not supply;
4. **energy:** PSO-SA optimizes active + idle node energy, while Dataset-v1's authoritative primary compute-energy metric excludes system-wide idle energy.

It also treats IoT primarily as the request-generating layer, rather than as the same kind of task-execution tier materialized by the research dataset.

## Why adding budget would be scientifically wrong

Possible modifications such as:

- rejecting particles above `budget_ncu`;
- adding cost to the fitness function;
- introducing a budget penalty;
- repairing over-budget mappings;
- distributing workflow budget to tasks;

are all substantial new algorithmic mechanisms. They are not described by this PSO-SA paper. Implementing one would create a novel PSO-SA-derived hybrid and then compare that hybrid as though it were the published baseline, which the benchmark methodology forbids.

## Faithfulness classification

**NOT SUITABLE AS A PRIMARY JOINT DEADLINE-BUDGET IFC-V1 COMPARATOR**

No production PSO-SA scheduler is added to the primary benchmark registry.

This is a **problem-definition mismatch**, not a quality judgment about the paper. PSO-SA is directly relevant literature for energy/deadline scheduling in fog/cloud environments and should be cited when motivating energy-aware IFC scheduling, but it does not answer the same joint deadline-budget scheduling problem.

## Contextual research value

The paper remains useful for later analysis because it contributes mechanisms relevant to the IoT/fog/cloud setting:

- energy-aware scheduling;
- explicit task precedence during metaheuristic search;
- stochastic task prioritization;
- priority-weighted deadline-violation handling;
- hybrid global/local search;
- heterogeneous fog/cloud resource allocation.

These ideas may inform literature-gap analysis, but they must not be copied wholesale into the proposed algorithm merely to claim novelty.

## Optional future benchmark

PSO-SA would be an appropriate comparator in a separate benchmark whose public instance contract includes:

- per-task deadlines;
- per-task priorities;
- the paper's active/idle energy model;
- fog/cloud processing-node semantics;
- no required monetary-budget constraint, or a separately published budget-aware extension.

## Audit gate outcome

- Full paper available: **yes**.
- IoT/fog/cloud relevance: **yes**.
- Workflow/DAG scheduling: **yes**.
- Energy objective: **yes**.
- Deadline handling: **yes, per task / priority-aware**.
- Monetary budget constraint: **no**.
- Required per-task deadline data present in frozen IFC input: **no**.
- Required per-task priority data present in frozen IFC input: **no**.
- Paper energy metric identical to Dataset-v1: **no**.
- Implement in primary joint deadline-budget registry: **no**.
