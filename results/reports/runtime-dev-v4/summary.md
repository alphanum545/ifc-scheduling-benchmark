# Report: runtime-dev-v4

Instance set: **dev**. Algorithms: HEFT-IFC, PEFT-IFC, BDHEFT (a=0.5), DBCS, BDSD, BDDC (w=0.5), BDC (w=0.5), BDCWS, DCR-v0, DCR-v0 (optimized), DCR-v1 (full ranking), DCR-v1 Admission, DCR-v3 Rescue, DCR-v4 (reserve + quality ranking), DCR-v4R (v4 + v3 rescue). Highlight: DCR-v4 (reserve + quality ranking). Cases: 160 selected, **0 compared** (every selected algorithm valid, and deterministic where checked).

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 160 | 160 | 0 | 0 | 0 | 0 |
| PEFT-IFC | 160 | 160 | 0 | 0 | 0 | 0 |
| BDHEFT (a=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |
| DBCS | 160 | 160 | 0 | 0 | 0 | 0 |
| BDSD | 160 | 160 | 0 | 0 | 0 | 0 |
| BDDC (w=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDC (w=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDCWS | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v0 | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v0 (optimized) | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v1 (full ranking) | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v1 Admission | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v3 Rescue | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v4 (reserve + quality ranking) | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v4R (v4 + v3 rescue) | 0 | 0 | 0 | 0 | 0 | 160 |

No case has a valid run for every selected algorithm.
