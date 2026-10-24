"""Weight-tuned comparator variants for the paper-1 tuning study (docs/proposed/EXPERIMENTS_PAPER1.md).

Each class only overrides the comparator's published weight; the audited comparator code
(algorithms/bddc_bdc, algorithms/bdheft) is imported unchanged. The 0.5 setting is the
existing registered comparator and is not duplicated here.
"""
from algorithms.bddc_bdc import BDCScheduler, BDDCScheduler
from algorithms.bdheft import BDHEFTScheduler

WEIGHTS = ((1, 10), (3, 10), (7, 10), (9, 10))


def _variant(base, prefix: str, attr: str, num: int, den: int):
    tag = f"{num:02d}" if den == 10 else f"{num}_{den}"
    ident = f"{prefix}{tag}"
    return type(f"{base.__name__}_{tag}", (base,), {
        "algorithm_id": ident,
        "algorithm_version": f"{base.algorithm_version}_weight_{num}_{den}",
        f"{attr}_numerator": num, f"{attr}_denominator": den,
    })


_classes = {}
for _n, _d in WEIGHTS:
    for _base, _prefix, _attr in ((BDCScheduler, "bdc_ifc_w", "omega"), (BDDCScheduler, "bddc_ifc_w", "omega"),
                                  (BDHEFTScheduler, "bdheft_ifc_a", "alpha")):
        _cls = _variant(_base, _prefix, _attr, _n, _d)
        _classes[_cls.__name__] = _cls
globals().update(_classes)
__all__ = sorted(_classes)
