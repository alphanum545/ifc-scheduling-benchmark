from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent / "historical"))

from algorithms.pacm import PACMScheduler
from experiment.evaluator_adapter import evaluate_decision
from test_dcr_ifc import fixture, inp


def test_critical_chain_uses_earliest_finish_even_if_costlier():
    base = fixture([[10, 2]] * 2, [[1, 9]] * 2, [(0, 1)])
    case = inp(base, 100)
    decision = PACMScheduler().schedule(case)
    assert set(decision.resource_assignments.values()) == {"R01"}
    assert evaluate_decision(case, decision).schedule["makespan_us"] == 4


def test_noncritical_task_uses_cheapest_slot_that_meets_bound():
    base = fixture([[90, 100], [2, 10]], [[3, 9], [9, 1]])
    case = inp(base, 200)
    decision = PACMScheduler().schedule(case)
    assert decision.resource_assignments == {"T00": "R00", "T01": "R01"}
    assert evaluate_decision(case, decision).deadline_feasible


def test_tied_critical_paths_and_zero_variance():
    base = fixture([[1, 9], [9, 1]], [[9, 1], [1, 9]])
    case = inp(base, 1)
    decision = PACMScheduler().schedule(case)
    assert decision.resource_assignments == {"T00": "R00", "T01": "R01"}
    assert evaluate_decision(case, decision).deadline_feasible


def test_impossible_deadline_and_repeatable_seed():
    case = inp(fixture([[8, 25],[9, 4],[12, 2]], [[1, 9]]*3,
                       [(0, 2),(1, 2)], bits=1000), 1)
    first = PACMScheduler(7).schedule(case)
    assert PACMScheduler(7).schedule(case) == first
    assert not evaluate_decision(case, first).deadline_feasible
