"""Pacing policies used as members of the option-A rescue portfolio.

Each member is the champion loop (`_DCRV2Base`) with one O(1)-per-candidate filter over
the champion-admitted candidates of a step (complexity option B within a single run).
They reproduce the throwaway probes in scripts/probe_budget_pacing.py ("tasks") and
scripts/probe_adaptive_pacing.py. See reports/dcr-v2-core-evidence.md.
"""
from __future__ import annotations

from fractions import Fraction

from .dcr_v2 import DeadlineCertainlyLost, _DCRV2Base  # noqa: F401  (re-exported)
from .dcr_v2_rules import pressure_safe, task_pacing_admits


def fraction_label(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


class TaskPacingScheduler(_DCRV2Base):
    """Extra spend may not outrun alpha * (share of tasks scheduled) of the initial slack."""

    def __init__(self, alpha: Fraction) -> None:
        self.alpha = Fraction(alpha)
        tag = f"{self.alpha.numerator}_{self.alpha.denominator}"
        self.algorithm_id = f"dcr_ifc_v2_task_pacing_{tag}"
        self.algorithm_version = f"{self.algorithm_id}_design_20260930_impl1"

    def _filter_admitted(self, st, i, screened, stats):
        md = st.model
        total = sum(md.cmin)
        committed = total - st.raw_reserve + md.cmin[i]
        done, whole = len(st.order) + 1, len(md.tasks)
        ok = [item for item in screened
              if task_pacing_admits(st.spent + md.c[i][item[1]] - committed, done=done,
                                    whole=whole, slack0=md.B - total, alpha=self.alpha)]
        if ok:
            return ok
        stats['pace_override_steps'] = stats.get('pace_override_steps', 0) + 1
        cheapest = min((item[1] for item in screened), key=lambda r: (md.c[i][r], r))
        return [item for item in screened if item[1] == cheapest]


class PressureGatedScheduler(_DCRV2Base):
    """Save (cheapest safe option) when finish <= D - kappa*h[i]; otherwise champion ranking."""

    def __init__(self, kappa: Fraction) -> None:
        self.kappa = Fraction(kappa)
        tag = f"{self.kappa.numerator}_{self.kappa.denominator}"
        self.algorithm_id = f"dcr_ifc_v2_pressure_gated_{tag}"
        self.algorithm_version = f"{self.algorithm_id}_design_20260930_impl1"

    def _filter_admitted(self, st, i, screened, stats):
        md = st.model
        # screened items are ((max_loss, min_loss, finish, cost, r), r)
        safe = [item for item in screened
                if pressure_safe(item[0][2], deadline=md.D, tail=md.h[i], kappa=self.kappa)]
        if not safe:
            stats['adaptive_spend_steps'] = stats.get('adaptive_spend_steps', 0) + 1
            return screened
        stats['adaptive_save_steps'] = stats.get('adaptive_save_steps', 0) + 1
        return [min(safe, key=lambda item: (item[0][3], item[0][2], item[1]))]
