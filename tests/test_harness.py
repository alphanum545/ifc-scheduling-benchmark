"""Tests for the benchmark harness (registry, dataset manifest, replay checker, planning)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import bench  # noqa: E402
import data  # noqa: E402
import verify_replay  # noqa: E402


def test_every_registered_algorithm_loads_and_matches_its_reference_identity():
    reg = bench.registry()
    refs = verify_replay.load_references()
    for name, spec in reg.items():
        sched = bench.load_scheduler(spec)
        assert sched.algorithm_id and sched.algorithm_version
        targets = spec.get("reference", [])
        for t in [targets] if isinstance(targets, str) else targets:
            assert t in refs, f"{name}: reference set {t} missing"
            if t.startswith("primary:"):
                versions = {r["algorithm_version"] for r in refs[t].values()}
                assert versions == {sched.algorithm_version}, (name, versions)


def test_source_hash_changes_when_a_source_file_changes(tmp_path, monkeypatch):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("x = 1\n")
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    h1 = bench.source_hash(["pkg"])
    (tmp_path / "pkg" / "a.py").write_text("x = 2\n")
    assert bench.source_hash(["pkg"]) != h1


def test_manifest_is_development_only_and_holdout_free():
    man = data.manifest()
    assert man["split_counts"] == {"development": 160}
    assert len(man["entries"]) == 160 and all(e["split"] == "development" for e in man["entries"])
    assert "calibration_entries" not in man
    bases = {b["base_instance_id"] for b in man["base_entries"]}
    assert {e["base_instance_id"] for e in man["entries"]} == bases
    assert all(e["path"].startswith("instances/development/") for e in man["entries"])


def test_suites_are_subsets_of_the_development_manifest():
    ids = {e["instance_id"] for e in data.manifest()["entries"]}
    for name, n in (("smoke5", 5), ("core24", 24)):
        suite = json.loads((ROOT / "manifests" / "suites" / f"{name}.json").read_text())
        got = {e["candidate_id"] for e in suite["entries"]}
        assert len(got) == n and got <= ids


def test_regeneration_shards_cover_every_base_once():
    man = data.manifest()
    shards = data.shard_groups(man, 20)
    seen = [b for s in shards for b, _ in s]
    assert sorted(seen) == sorted({b["base_instance_id"] for b in man["base_entries"]})


def test_replay_checker_flags_a_changed_outcome():
    ref = next(iter(verify_replay.load_references()["primary:bdc_ifc_w05"].values()))
    row = {k: str(ref[k]) for k in ("schedule_id", "makespan_us", "compute_cost_ncu", "compute_energy_nj",
                                    "network_energy_pj", "joint_feasible", "deadline_met", "budget_met")}
    assert verify_replay.compare(row, ref) == []
    row["makespan_us"] = str(int(row["makespan_us"]) + 1)
    assert verify_replay.compare(row, ref)
    row["makespan_us"] = str(ref["makespan_us"])
    row["joint_feasible"] = str(not ref["joint_feasible"])
    assert verify_replay.compare(row, ref)


def test_reference_results_reproduce_the_published_counts():
    refs = verify_replay.load_references()
    counts = {k.split(":", 1)[1]: sum(r["joint_feasible"] for r in v.values())
              for k, v in refs.items() if k.startswith("primary:")}
    assert counts == {"bdc_ifc_w05": 120, "bdsd_ifc": 94, "dbcs_ifc": 76, "bdheft_ifc_a05": 72,
                      "bddc_ifc_w05": 38, "deterministic_heft_ifc": 8, "deterministic_peft_ifc": 1}
    assert sum(r["joint_feasible"] for r in refs["dcr:dcr_ifc_v1_arrival_admission"].values()) == 140


def test_plan_skips_runs_already_in_the_store(tmp_path, monkeypatch):
    reg = bench.registry()
    inst = data.manifest()["entries"][0]["instance_id"]
    monkeypatch.setattr(bench, "STORE", tmp_path / "store.csv")
    monkeypatch.setattr(bench, "STORE_DIR", tmp_path / "store")
    bench.write_store([{"algo": "bdc", "source_sha256": reg["bdc"]["source_sha256"], "instance_id": inst,
                        "status": "ok", "reps": 2}])
    assert (tmp_path / "store" / "bdc.csv").exists()
    monkeypatch.setattr(bench, "WORK", tmp_path)
    args = type("A", (), dict(set="dev", algos="bdc", suite="all", families="all", tasks="all", qos="all",
                              reps=2, workers=0, shards=4, force=False, github_output=None))
    bench.cmd_plan(args)
    plan = json.loads((tmp_path / "plan.json").read_text())
    planned = {w["instance_id"] for s in plan["shards"] for w in s}
    assert inst not in planned and len(planned) == 159


def test_expansion_manifest_is_disjoint_from_the_pilot_development_set():
    dev, exp = data.manifest("dev"), data.manifest("expansion")
    assert exp["instance_count"] == 1890 and len(exp["entries"]) == 1890
    assert all(e["split"] == "expansion_evaluation" for e in exp["entries"])
    assert not {e["instance_id"] for e in exp["entries"]} & {e["instance_id"] for e in dev["entries"]}
    assert not {b["base_instance_id"] for b in exp["base_entries"]} & {b["base_instance_id"] for b in dev["base_entries"]}
    assert {e["base_instance_id"] for e in exp["entries"]} == {b["base_instance_id"] for b in exp["base_entries"]}


def test_expansion_reference_covers_every_instance_for_eight_algorithms():
    refs = verify_replay.load_references()
    exp = [k for k in refs if k.startswith("expansion:")]
    assert len(exp) == 8 and all(len(refs[k]) == 1890 for k in exp)


def test_store_migrates_from_the_legacy_file_to_per_algorithm_files(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "STORE", tmp_path / "store.csv")
    monkeypatch.setattr(bench, "STORE_DIR", tmp_path / "store")
    legacy = [{"algo": a, "source_sha256": "s", "instance_id": f"i{k}", "status": "ok", "reps": 1}
              for a in ("bdc", "dbcs") for k in range(3)]
    bench._write_csv(legacy, tmp_path / "store.csv")
    newer = {"algo": "bdc", "source_sha256": "s", "instance_id": "i0", "status": "error", "reps": 1}
    bench._write_csv([newer], tmp_path / "store" / "bdc.csv")
    rows = bench.read_store()
    assert len(rows) == 6 and [r for r in rows if r["instance_id"] == "i0" and r["algo"] == "bdc"][0]["status"] == "error"
    bench.write_store(rows)
    assert bench.read_store(tmp_path / "store.csv") == []  # header-only placeholder
    assert sorted(p.name for p in (tmp_path / "store").glob("*.csv")) == ["bdc.csv", "dbcs.csv"]
    assert sorted((r["algo"], r["instance_id"], r["status"]) for r in bench.read_store()) == sorted(
        (r["algo"], r["instance_id"], r["status"]) for r in rows)
