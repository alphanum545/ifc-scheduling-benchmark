from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent / "historical"))

from algorithms.dcds import DCDSScheduler
from experiment.evaluator_adapter import evaluate_decision
from test_dcr_ifc import fixture, inp


def run(base, deadline):
    case = inp(base, D=deadline)
    decision = DCDSScheduler().schedule(case)
    return decision, evaluate_decision(case, decision)


def test_edge_deadline_equality_and_cheapest_placement():
    base = fixture([[5, 3, 1]], [[2, 4, 9]], tiers=["iot", "fog", "cloud"])
    decision, result = run(base, 5)
    assert decision.resource_assignments == {"T00": "R00"}
    assert decision.internal_statistics["offloading_set_size"] == 0
    assert result.deadline_feasible


def test_offload_propagates_to_predecessor_on_chain():
    base = fixture([[10, 2]] * 3, [[1, 9]] * 3, [(0, 1), (1, 2)], tiers=["fog", "cloud"])
    decision, result = run(base, 6)
    assert decision.internal_statistics["offloading_set_size"] == 3
    assert result.schedule["makespan_us"] == 6
    assert result.deadline_feasible


def test_parallel_cloud_tasks_contend_for_one_slot():
    base = fixture([[12, 4]] * 2, [[1, 9]] * 2, tiers=["fog", "cloud"])
    decision, result = run(base, 5)
    assert decision.internal_statistics["offloading_set_size"] == 2
    assert result.schedule["makespan_us"] == 8
    assert not result.deadline_feasible
