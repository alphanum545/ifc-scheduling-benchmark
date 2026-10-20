# IFC scheduling benchmark

Runs workflow-scheduling algorithms for **IoT–Fog–Cloud (IFC) systems under a joint deadline and budget**
in the cloud (GitHub Actions), checks every schedule with the benchmark's own evaluator, and produces results
tables and paper-ready figures.

- **Exact code, not re-implementations.** The seven comparators and the DCR line are byte-identical copies of
  the sources that produced the original experiments. `provenance/SOURCES.json` lists each file's SHA-256
  and origin.
- **No data in the repository.** The 160 development instances are regenerated in CI from the public
  [Dataset](https://github.com/alphanum545/Dataset) repository and checked byte for byte against the frozen
  hashes in `manifests/dev-v1.json`. The 40 protected holdout instances are never generated here.
- **Replay-checked.** Every run is compared field by field with the historical result for the same algorithm
  version and instance (`reference/`, `tools/verify_replay.py`). Any mismatch is reported in `results/replay.md`.
- **Fast.** Work is split across up to 20 machines. Only runs not done before are executed, and an algorithm
  reruns automatically when any of its source files change.

---

## Instance sets

| Set | Manifest | Instances | What it is |
|---|---|---:|---|
| `dev` | `manifests/dev-v1.json` | 160 | development split of the 200-input pilot (159 base configurations) |
| `expansion` | `manifests/expansion-v1.json` | 1,890 | frozen `ifc-expansion-selection-v1` cohort: 630 new base configurations × 3 QoS levels, disjoint from every pilot instance and base. Same 105 source workflows, so it tests new infrastructure/seed/QoS configurations, not unseen DAGs |

The 40 protected holdout instances of the pilot are in neither set.

## One-time setup

**Actions** tab → **Prepare data** → **Run workflow**, once with `set = dev` and once with `set = expansion`.
Each run rebuilds the set's instances on 20 machines, verifies every file against the frozen hashes in its
manifest (byte-identical for `dev`, content-identical for `expansion`, whose frozen files used a different JSON
layout), and publishes the release asset `data/ifc-<set>-v1.zip`. Rerun only if a manifest changes.

## Running a benchmark

**Actions** tab → **Benchmark** → **Run workflow**, then fill in:

| Field | Example | Meaning |
|---|---|---|
| set | `dev` or `expansion` | instance set |
| algos | `all` or `bdc,dcr-v1-admission` | IDs from `algorithms.toml` |
| highlight | `dcr-v1-admission` | the proposed algorithm: drawn first, gains/losses computed against it |
| suite | `smoke`, `core`, `all` | `dev` only: 5 cases, the fixed 24-case core set, or all 160. Use `all` for `expansion` |
| families | `all` or `montage,sipht` | workflow families (CyberShake, Genome, LIGO, Montage, SIPHT) |
| tasks | `all` or `60,1000` | task counts (60, 100, 200, 400, 600, 800, 1000) |
| qos | `all` or `tight` | QoS profile: relaxed, moderate, tight |
| reps | `1` | repetitions per run; 2 or more also re-observes determinism (the replay check covers it either way) |
| workers | `0` | parallel instance processes per machine: 0 = all cores (fastest); 1 = one at a time, for a clean runtime study |
| report_name | `dev-all` | folder name for this report |
| shards | `60` | number of jobs; 20 run at a time on the free plan, the rest queue. Each job saves after every instance and resumes if rerun |
| force | off | rerun everything, ignoring stored results |

When it finishes, the run page shows the summary. The report is committed to `results/reports/<report_name>/`
and attached to the run as a downloadable artifact.

### What a report contains

| File | Contents |
|---|---|
| `summary.md` | validity, joint/deadline/budget feasibility, runtime and paired runtime ratios, feasibility by family / tasks / QoS / scenario / scale, pairwise gains and losses against the highlighted algorithm, replay check |
| `summary.xlsx` | the same tables plus every run, one sheet each |
| `results.csv` | one row per run used in the report |
| `replay.md` | exact-match check against the historical results |
| `figures/*.pdf, *.png` | joint feasibility; feasibility by dimension; feasibility and runtime vs. tasks; runtime ratio ECDF; gains/losses |

Comparisons use only cases where **every** selected algorithm produced a valid, deterministic schedule, so all
algorithms are compared on the same cases. The Validity table says what was left out and why. All runs ever
made are kept in `results/store.csv`. A report can be rebuilt at any time without rerunning anything.

---

## Algorithms

| ID | Algorithm | Role | Source |
|---|---|---|---|
| `heft-ifc`, `peft-ifc` | HEFT, PEFT (deadline/budget-agnostic references) | comparator | Dataset reference schedulers |
| `bdheft` | BDHEFT, α = 0.5 (Verma & Kaushal, 2015) | comparator | minor IFC adaptation |
| `dbcs` | DBCS (Arabnejad, Barbosa & Prodan, 2016) | comparator | minor IFC adaptation |
| `bdsd` | BDSD (Sun, Xiao & Xu, 2019) | comparator | minor IFC adaptation |
| `bddc`, `bdc` | BDDC / BDC, ω = 0.5 (Taghinezhad-Niar, Pashazadeh & Taheri, 2021) | comparator | **major** IFC adaptation |
| `dcr-v0`, `dcr-v0-opt` | DCR v0 and its decision-identical optimization | proposed (history) | |
| `dcr-v1`, `dcr-v1-admission` | DCR v1 with child-arrival reserve: full ranking / admission only | proposed | |
| `dcr-v3-rescue` | DCR v3: v1 Admission plus a bounded rescue portfolio | proposed (candidate) | |

The adaptations are documented, equation by equation, in `docs/paper_audits/`. The fixed IFC model has a
materialized set of resources. Billing-cycle cost and elastic instance provisioning from the BDC/BDDC paper
are therefore **not** preserved, and ω = 0.5 is not that paper's default. The run metadata records this.

### Adding an algorithm

1. Put a Python package under `algorithms/` or `ifc_algorithms/` with a class implementing
   `algorithms.common.interface.Scheduler`. The class has an `algorithm_id` and `algorithm_version`, and a
   `schedule(scheduling_input)` method that returns an `AlgorithmDecision` (task order and task→resource
   mapping only).
2. Add a block to `algorithms.toml` with `module`, `class`, `role` and `sources`.
3. Commit, then run **Benchmark** with `algos` = your ID (or `all`). Only the new algorithm runs; the
   others come from the store.

The scheduler sees only the public instance, deadline and budget. The schedule is built and scored afterwards
by the pinned Dataset evaluator (`generator.schedule.build_schedule`) and re-checked with
`generator.schedule.evaluate_schedule`. Policy time is measured around `schedule()` only.

## Metrics

- **Joint feasibility**: makespan ≤ deadline **and** compute cost ≤ budget. This is the primary outcome.
- **Deadline met** and **budget met** separately; **makespan** (µs), **compute cost** (nCU), compute energy (nJ),
  network energy (pJ), all as exact integers from the evaluator.
- **Scheduling time**: policy time per case, the median over repetitions. Runtime ratios are paired: same case,
  same machine, rotating run order.

## Development / holdout

The dataset has 200 inputs: 160 development and 40 protected holdout. This repository contains, regenerates
and runs **only the development split**. All results here are therefore development (in-sample) results.
The holdout is reserved for one final evaluation of a frozen candidate.

## Running locally (optional)

Needs Python 3.11+.

```
pip install -r requirements.txt matplotlib openpyxl
git clone https://github.com/alphanum545/Dataset .dataset && git -C .dataset checkout 5266acbfb246a7354929330f1329227609ec1c06
python3 tools/data.py regen --dataset-repo .dataset --out data          # or: python3 tools/data.py fetch --out data
python3 tools/bench.py plan --suite smoke --shards 1
python3 tools/bench.py run --data data --shard 0 --out .work/shard-0.csv
python3 tools/bench.py merge --inputs ".work/shard-*.csv"
python3 tools/report.py --suite smoke --name local-test
python3 tools/verify_replay.py
```

## Layout

```
algorithms.toml              algorithm registry
algorithms/                  comparators and DCR v0/v1 (exact historical sources)
ifc_algorithms/proposed/     DCR v2 members and DCR v3 Rescue (exact historical sources)
experiment/                  historical runner/evaluator adapter used by the historical tests
manifests/dev-v1.json        the 160 development instances and 159 base instances, with SHA-256
manifests/expansion-v1.json  the 1,890 expansion instances and 630 base instances, with SHA-256 and content hashes
manifests/suites/            smoke (5) and core (24) case lists
reference/                   historical results used by the replay check (primary 1,120; DCR runs; expansion
                             15,120 = expansion-1890-results.jsonl.gz) and the AWS runtime study (aws-runtime.json)
provenance/SOURCES.json      SHA-256 and origin of every algorithm source file
tools/data.py                regenerate / pack / fetch / verify the dataset
tools/bench.py               plan, run, merge
tools/report.py              tables and figures
tools/verify_replay.py       exact-match check against reference/
results/store.csv            every run ever made
results/reports/<name>/      reports
docs/paper_audits/           comparator paper audits and adaptation decisions
docs/proposed/               DCR v0/v1 specifications
.github/workflows/           Tests, Prepare data, Benchmark
```

The pinned Dataset code commit is `67489dc2f3009c394a0bc783181612fe6481efaf` (evaluator). The instances
were generated at `5266acbfb246a7354929330f1329227609ec1c06`, which differs from it only in a freeze-record
file.
