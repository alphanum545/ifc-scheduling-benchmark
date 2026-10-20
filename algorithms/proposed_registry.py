"""Proposed-method registry; the frozen seven-comparator registry is untouched."""
from algorithms.common.registry import AlgorithmRegistry
from algorithms.dcr_ifc import DCRScheduler


def proposed_registry() -> AlgorithmRegistry:
    return AlgorithmRegistry((DCRScheduler(),))
