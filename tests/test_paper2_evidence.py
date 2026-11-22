"""Exercise one real shard and the reporting path on small, isolated fixtures."""

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests" / "historical")]
import bench
import paper2_evidence as ev
import paper2_report as report
from test_dcr_ifc import fixture


def test_pipeline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    actual_sources = ev.sources()
    cached = {}
    monkeypatch.setattr(ev, "stored", lambda _: cached)
    base = fixture(
        [[4, 3, 1], [5, 2, 1], [3, 2, 1]],
        [[0, 4, 9], [0, 5, 8], [0, 6, 9]],
        [(0, 2), (1, 2)],
    )
    entries = {}
    protocol = {
        "sources": actual_sources,
        "cohorts": {},
        "jobs": [],
        "execution_commit": "smoke",
    }
    ev.OUT.mkdir()
    for name in ev.SETS:
        i = f"sample-{name}"
        root = Path("data") / name
        root.mkdir(parents=True)
        (root / "base.json").write_text(json.dumps(base))
        (root / "qos.json").write_text(
            json.dumps(
                {
                    "instance_id": i,
                    "base_instance_id": "synthetic-dcr",
                    "deadline": {"deadline_us": 20},
                    "budget": {"budget_ncu": 30},
                }
            )
        )
        entry = {
            "instance_id": i,
            "base_instance_id": "synthetic-dcr",
            "path": "qos.json",
            "family": "fixture",
            "target_task_count": 3,
            "qos_profile": "tight",
            "scenario_profile": "test",
            "replicate_id": "r1",
            "resource_scale": "s1",
            "source_sha256": "frozen-fixture",
        }
        entries[name] = {
            "entries": [entry],
            "base_entries": [
                {"base_instance_id": "synthetic-dcr", "path": "base.json"}
            ],
        }
        protocol["jobs"] += ev.case_matrix([entry], name, 2)
        protocol["cohorts"][name] = {
            "controls": sorted(ev.study_ids([entry])),
            "manifest_sha256": ev.digest(
                ROOT / "manifests" / bench.SET_MANIFESTS[name]
            ),
        }
    monkeypatch.setattr(bench, "manifest", lambda s: entries[s])
    protocol["exact_csv_sha256"] = ev.digest(ROOT / "results/exact/exact-cost-60.csv")
    (ev.OUT / "protocol.json").write_text(json.dumps(protocol))
    for name in ev.SETS:
        ev.execute_shard(protocol, name, 0)
        _, rows = report.load_cohort(protocol, name)
        runs = next(iter(rows.values()))
        assert set(runs) == set(ev.STANDARD + ev.CONTROL)
        assert runs["equal-time-v2"]["budget_time_ns"] == runs[ev.V3]["runtime_ns"]
    # A complete checkpoint must not invoke a scheduler a second time.
    with monkeypatch.context() as mp:
        mp.setattr(
            bench, "_run_instance", lambda _: pytest.fail("rescheduled completed case")
        )
        ev.execute_shard(protocol, "unseen", 0)
    monkeypatch.setattr(report, "historical_sample", lambda entries, rows, dest: None)
    report.report(protocol)
    assert len(list(csv.DictReader((ev.OUT / "bundle" / "runs.csv").open()))) == 2 * (
        len(ev.STANDARD) + 3
    )
    for fname in [
        "summary.md",
        "coverage.csv",
        "runtime.csv",
        "comparisons.csv",
        "cp-sat.csv",
        "sha256.json",
    ]:
        assert (ev.OUT / "bundle" / fname).is_file()

    path = ev.OUT / "rows-unseen-0.csv"
    with path.open() as fp:
        rows = list(csv.DictReader(fp))
    with path.open("w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=ev.FIELDS)
        w.writeheader()
        w.writerows(rows[:-1])
    with pytest.raises(ValueError, match="invalid paired matrix"):
        report.load_cohort(protocol, "unseen")


def test_timeout_and_missed_deadline_are_counted():
    def row(cost, met="True", available=""):
        return {
            "compute_cost_ncu": str(cost),
            "deadline_met": met,
            "available_by_cutoff": available,
        }

    rows = {
        "a": {ev.V3: row(4), "other": row(6)},
        "b": {ev.V3: row(2), "other": row(1, available="False")},
        "c": {ev.V3: row(8, "False"), "other": row(9)},
    }
    e = {k: {"source_sha256": k} for k in rows}
    assert report.comparison(e, rows, list(rows), "other")[:8] == [
        3,
        2,
        2,
        1,
        1,
        0,
        0,
        1,
    ]
