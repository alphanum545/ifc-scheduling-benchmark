# Paper 1: joint deadline–budget feasibility (DCR)

- `EVIDENCE_PACK.md` collects every result, test, proof sketch, threat and claim wording for the paper.
- `results/` holds the generated result tables. `figures/` holds the tightness-grid heatmap.
- `analysis/` holds the scripts that recompute everything from `results/store.csv`, `results/robustness/` and `results/exact/`. They need numpy and scipy, and run no scheduler.

```
python3 docs/paper1/analysis/stats.py . out            # main sets: CIs, McNemar, quality, runtime
python3 docs/paper1/analysis/ablations.py . out/abl.md # component ablations
python3 docs/paper1/analysis/experiments.py . out      # unseen, tuning, grid, robustness, exact
python3 docs/paper1/analysis/heatmap.py out/grid_heatmap.json out/grid_heatmap
```

Protocols, each fixed before its run: `docs/proposed/ABLATIONS_PAPER1.md` and `docs/proposed/EXPERIMENTS_PAPER1.md`.
