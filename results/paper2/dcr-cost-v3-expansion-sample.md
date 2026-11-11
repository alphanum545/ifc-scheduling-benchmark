Sample: 495 of 495 planned instances of `expansion` (all 60-task instances plus a fixed selection of the others: step 12, see the tool's docstring).

Larger instances by QoS: tight 45, moderate 135, relaxed 45.
- Valid runs (evaluator rebuild equals independent re-check): dcr-cost-v3 495/495.
- dcr-cost-v3 meets D on 495/495.
- Reproduction of the stored CI runs: local dcr-cost-v2 equals the stored schedule (hash, makespan, cost) on 495/495 instances.

### Cost: DCR-Cost v3 ÷ competitor (instances where both meet D)

| group | vs | n | median | mean | p10 | v3 wins / ties / losses | sign p |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| all | DCR-Cost v2 (stored CI run) | 495 | 1.000 | 0.971 | 0.929 | 291 / 204 / 0 | 5.0e-88 |
| all | DCR-Cost v1 | 495 | 0.965 | 0.870 | 0.562 | 411 / 84 / 0 | 3.8e-124 |
| all | ProLiS (seed 0) | 478 | 0.954 | 0.866 | 0.541 | 453 / 22 / 3 | 1.7e-130 |
| all | IC-PCP | 456 | 0.514 | 0.516 | 0.116 | 454 / 0 / 2 | 1.1e-132 |
| tight | DCR-Cost v2 (stored CI run) | 135 | 0.997 | 0.975 | 0.919 | 90 / 45 / 0 | 1.6e-27 |
| moderate | DCR-Cost v2 (stored CI run) | 225 | 1.000 | 0.978 | 0.955 | 117 / 108 / 0 | 1.2e-35 |
| relaxed | DCR-Cost v2 (stored CI run) | 135 | 1.000 | 0.953 | 0.827 | 84 / 51 / 0 | 1.0e-25 |
| 60 tasks | DCR-Cost v2 (stored CI run) | 270 | 1.000 | 0.972 | 0.917 | 135 / 135 / 0 | 4.6e-41 |
| 100 tasks | DCR-Cost v2 (stored CI run) | 40 | 0.999 | 0.958 | 0.891 | 25 / 15 / 0 | 6.0e-08 |
| 200 tasks | DCR-Cost v2 (stored CI run) | 35 | 0.999 | 0.983 | 0.921 | 24 / 11 / 0 | 1.2e-07 |
| 400 tasks | DCR-Cost v2 (stored CI run) | 40 | 0.999 | 0.981 | 0.973 | 31 / 9 / 0 | 9.3e-10 |
| 600 tasks | DCR-Cost v2 (stored CI run) | 35 | 0.999 | 0.978 | 0.969 | 26 / 9 / 0 | 3.0e-08 |
| 800 tasks | DCR-Cost v2 (stored CI run) | 40 | 0.999 | 0.953 | 0.933 | 27 / 13 / 0 | 1.5e-08 |
| 1000 tasks | DCR-Cost v2 (stored CI run) | 35 | 0.998 | 0.968 | 0.965 | 23 / 12 / 0 | 2.4e-07 |

### Against CP-SAT (60-task instances; best cost found in 5 min)

| method | n | ÷ C* median | mean | p90 | max | proven-optimal n | ÷ C* median there |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DCR-Cost v3 | 270 | 1.015 | 1.062 | 1.181 | 2.012 | 67 | 1.000 |
| DCR-Cost v2 | 270 | 1.027 | 1.103 | 1.306 | 2.230 | 67 | 1.013 |

### Policy runtime (s), same machine, same run

| tasks | n | v2 median | v3 median | v3 ÷ v2 median (paired) | v3 max |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 60 | 270 | 0.28 | 0.32 | 1.16 | 0.94 |
| 100 | 40 | 0.54 | 0.63 | 1.18 | 1.51 |
| 200 | 35 | 1.17 | 1.51 | 1.30 | 3.96 |
| 400 | 40 | 5.10 | 6.83 | 1.41 | 10.65 |
| 600 | 35 | 9.52 | 14.15 | 1.57 | 28.62 |
| 800 | 40 | 18.58 | 31.46 | 1.63 | 84.75 |
| 1000 | 35 | 32.67 | 51.29 | 1.81 | 175.25 |

CPU: Intel(R) Xeon(R) Processor @ 2.30GHz; 2 worker process(es); Python 3.13.18.
