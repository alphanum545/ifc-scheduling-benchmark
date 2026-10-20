from __future__ import annotations

from algorithms.bddc_bdc import BDCScheduler, BDDCScheduler
from algorithms.bdheft import BDHEFTScheduler
from algorithms.bdsd import BDSDScheduler
from algorithms.common.registry import AlgorithmRegistry
from algorithms.dbcs import DBCSScheduler
from algorithms.heft_ifc import HeftIFCScheduler
from algorithms.peft_ifc import PeftIFCScheduler


def stage2_registry() -> AlgorithmRegistry:
    """Return the deterministic Stage-2 reference algorithms."""
    return AlgorithmRegistry((HeftIFCScheduler(), PeftIFCScheduler()))


def stage3_registry() -> AlgorithmRegistry:
    """Return HEFT, PEFT, and the audited primary BDHEFT-0.5 comparator."""
    return AlgorithmRegistry(
        (HeftIFCScheduler(), PeftIFCScheduler(), BDHEFTScheduler())
    )


def stage4_registry() -> AlgorithmRegistry:
    """Return the deterministic baselines through the audited DBCS comparator."""
    return AlgorithmRegistry(
        (HeftIFCScheduler(), PeftIFCScheduler(), BDHEFTScheduler(), DBCSScheduler())
    )


def stage5_registry() -> AlgorithmRegistry:
    """Add the preregistered BDDC-IFC and BDC-IFC major adaptations."""
    return AlgorithmRegistry(
        (
            HeftIFCScheduler(),
            PeftIFCScheduler(),
            BDHEFTScheduler(),
            DBCSScheduler(),
            BDDCScheduler(),
            BDCScheduler(),
        )
    )


def stage8_registry() -> AlgorithmRegistry:
    """Return the seven primary fixed-IFC development comparators including BDSD."""
    return AlgorithmRegistry(
        (
            HeftIFCScheduler(),
            PeftIFCScheduler(),
            BDHEFTScheduler(),
            DBCSScheduler(),
            BDDCScheduler(),
            BDCScheduler(),
            BDSDScheduler(),
        )
    )
