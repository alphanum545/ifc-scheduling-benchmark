"""DCR-v4: deadline-aware reserve admission with weighted time-cost quality ranking.

Frozen 2026-10-27 (docs/proposed/DCR_V4_FREEZE_2026-10-27.md). DCR-v4 is DCR-v1 Admission's
deadline- and capacity-aware priced-reserve admission (with the exact child-arrival correction),
followed by ranking the admitted candidates by the weighted Quality of BDC (omega = 1/2):

    TQ = (b_i - FT - FT_min) / b_i          b_i = the task's latest finish (D minus critical tail)
    CQ = (RB  - TC - TC_min) / RB           RB  = B - spent (whole remaining budget; CQ = 0 if RB = 0)
    pick the highest (TQ + CQ) / 2; ties by (finish, cost, resource).

It is, by construction, the measured scoring-ablation variant `dcr-abl-bdc-score`: this class
reuses that step loop unchanged, so its decisions are identical (asserted in
tests/test_dcr_v4.py). Budget safety is inherited from the raw cheapest-remaining invariant.
"""
from __future__ import annotations

from algorithms.dcr_ablations_scoring.scheduler import _ScoringBase


class DCRV4QualityScheduler(_ScoringBase):
    algorithm_id = "dcr_ifc_v4_quality"
    algorithm_version = "dcr_ifc_v4_quality_freeze_20261027"
    rank = "bdc"
