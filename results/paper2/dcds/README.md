# DCDS fixed-pool benchmark

Only DCDS was executed in this extension. The two compressed CSVs contain one row per frozen instance with the schedule fingerprint, deadline, makespan, cost, validation flags and policy runtime. Both manifests were verified before execution. All 4,131 schedules passed the benchmark's independent replay evaluation. PACM results are pending access to its algorithm specification.

| Cohort | Attempted | DCDS met deadline | Both feasible | Mean v3 cost saving | Median v3 cost saving | v3 cheaper / tied / DCDS cheaper |
|---|---:|---:|---:|---:|---:|---:|
| Expansion | 1,890 | 1,398 | 1,398 | 19.41% | 4.69% | 1,375 / 20 / 3 |
| Unseen | 2,241 | 1,838 | 1,838 | 13.18% | 1.48% | 1,691 / 111 / 36 |

The reference is the archived v3 output in [run 45041750746](https://github.com/alphanum545/ifc-scheduling-benchmark/actions/runs/45041750746), artifact 14767864198. Its SHA-256 is `956fdca3c9011a127dd1d6dffabb4585ad46587d976239d0b89ddd21d470aaa7`. The cohort manifest digests and instance deadlines match. Savings are the mean or median of 100 × (DCDS cost − v3 cost) / DCDS cost on mutually deadline-feasible instances.

## Model and execution

Implementation commit `820da6f6b096ac84451c2e36ed040c0f244b5f90` adapts [Lou et al.](https://doi.org/10.1109/TMC.2022.3188770) to the IFC fixed resource pool. IoT and fog slots are local candidates. Virtual entry and exit transfers take zero time. The offloading queue uses an optimistic remaining-time estimate and reserves actual cloud slots in priority order. Multiple tasks assigned to the same cloud slot run serially. The cheaper-placement refinement checks successor start times. The shared evaluator reconstructs the final schedule from its priority order and resource mapping. These adaptations affect the measured deadline coverage.

Both runs used the pinned Dataset generator, NumPy 2.2.6, Python 3.12.14, eight worker processes, and one repetition per instance. The rows include raw runtime observations. Cross-run runtime ratios would require matched timing conditions.

For either cohort, fetch its frozen data using `tools/data.py fetch`, then run:

```sh
python tools/bench.py plan --set "$cohort" --algos dcds --reps 1 --shards 1 --workers 8
python tools/bench.py run --shard 0 --data "data/$cohort" --out "dcds-$cohort.csv"
```

Compressed CSV checksums (SHA-256):

- expansion.csv.gz — `0726b2feb92082dbf646b4701a9daf1e675ada28fad424159afa26fc6fb69011`
- unseen.csv.gz — `356ddd50dd5c417d22f8f75ba0f042626fca2f0b64a13e682d4acf21be54a835`
