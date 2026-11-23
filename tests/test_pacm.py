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


def test_indegree_term_changes_noncritical_placement():
    # Task 2 can finish on R01 at 10.05 s. Eq. 19 would give it 10 s,
    # while Eq. 22 gives about 10.106 s for the in-degrees [0, 1, 1].
    base = fixture([[1_000_000, 12_000_000, 12_000_000],
                    [99_000_000, 120_000_000, 120_000_000],
                    [8_000_000, 9_050_000, 2_000_000]],
                   [[1, 2, 3], [1, 2, 3], [8, 1, 5]], [(0, 1), (0, 2)])
    decision = PACMScheduler().schedule(inp(base, 10_000_000))
    assert decision.resource_assignments["T02"] == "R01"
