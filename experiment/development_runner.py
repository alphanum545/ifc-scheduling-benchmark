"""Excerpt of the historical experiment.development_runner (benchmark commit 7bcefcf).

Only the preregistered comparator identity tuple is kept; the AWS/S3 development
orchestration in the original module is not part of this public repository. The
constant is copied verbatim so tests/historical/test_dcr_ifc.py runs unchanged.
"""

FROZEN_PRIMARY_COMPARATOR_IDS = (
    "bdc_ifc_w05",
    "bddc_ifc_w05",
    "bdheft_ifc_a05",
    "bdsd_ifc",
    "dbcs_ifc",
    "deterministic_heft_ifc",
    "deterministic_peft_ifc",
)
