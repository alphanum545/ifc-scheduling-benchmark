# Report: grid-all-v4

Instance set: **grid**. Algorithms: HEFT-IFC, PEFT-IFC, BDHEFT (a=0.5), DBCS, BDSD, BDDC (w=0.5), BDC (w=0.5), BDCWS, DCR-v0, DCR-v0 (optimized), DCR-v1 (full ranking), DCR-v1 Admission, DCR-v3 Rescue, DCR-v4 (reserve + quality ranking), DCR-v4R (v4 + v3 rescue). Highlight: DCR-v4 (reserve + quality ranking). Cases: 3975 selected, **0 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 55650 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 3975 | 3975 | 0 | 0 | 0 | 0 |
| PEFT-IFC | 3975 | 3975 | 0 | 0 | 0 | 0 |
| BDHEFT (a=0.5) | 3975 | 3975 | 0 | 0 | 0 | 0 |
| DBCS | 3975 | 3975 | 0 | 0 | 0 | 0 |
| BDSD | 3975 | 3975 | 0 | 0 | 0 | 0 |
| BDDC (w=0.5) | 3975 | 3975 | 0 | 0 | 0 | 0 |
| BDC (w=0.5) | 3975 | 3975 | 0 | 0 | 0 | 0 |
| BDCWS | 3975 | 3975 | 0 | 0 | 0 | 0 |
| DCR-v0 | 3975 | 3975 | 0 | 0 | 0 | 0 |
| DCR-v0 (optimized) | 3975 | 3975 | 0 | 0 | 0 | 0 |
| DCR-v1 (full ranking) | 3975 | 3975 | 0 | 0 | 0 | 0 |
| DCR-v1 Admission | 3975 | 3975 | 0 | 0 | 0 | 0 |
| DCR-v3 Rescue | 3975 | 3975 | 0 | 0 | 0 | 0 |
| DCR-v4 (reserve + quality ranking) | 3975 | 3975 | 0 | 0 | 0 | 0 |
| DCR-v4R (v4 + v3 rescue) | 0 | 0 | 0 | 0 | 0 | 3975 |

No case has a valid run for every selected algorithm.
