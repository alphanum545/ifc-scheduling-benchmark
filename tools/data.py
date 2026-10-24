#!/usr/bin/env python3
"""Rebuild, verify, pack and fetch the benchmark instance sets.

Two sets are defined, each by a manifest that lists every instance and base file with
its SHA-256:

  dev        manifests/dev-v1.json        160 development instances of the 200-input pilot
  expansion  manifests/expansion-v1.json  1,890 instances (630 new base configurations x 3 QoS)
                                           of the frozen ifc-expansion-selection-v1 cohort
  unseen     manifests/unseen-v1.json     2,241 instances of ifc-unseen-v1: 83 source DAGs no
                                           scheduler was designed on (35 new Bharathi replicates,
                                           48 WfCommons DAGs of 4 new families) x 27 configurations

The public repository ships no instance files. Each set is regenerated from the public
Dataset repository (alphanum545/Dataset) at the generator commit recorded in its manifest
and checked against the frozen hashes:
  dev        byte-identical files (sha256)
  expansion  identical content (content_sha256 = sha256 of generator.canonical.canonical_json_bytes),
             because the frozen expansion files were written with a different JSON layout
  unseen     byte-identical files (sha256). Its manifest is produced once by `freeze-build` /
             `freeze-merge` (workflow "Freeze unseen set") BEFORE any scheduler runs; a later
             independent regen must reproduce every byte.
The 40 protected holdout instances of the pilot are in neither manifest and are never generated.

  python3 tools/data.py regen  --set dev --dataset-repo ../Dataset --shard 0 --shards 20 --out .work/regen-0
  python3 tools/data.py pack   --set dev --inputs ".work/regen-*" --out .work/ifc-dev-v1.zip
  python3 tools/data.py fetch  --set dev --out data/dev          # download the release asset and verify
  python3 tools/data.py verify --set dev --data data/dev
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETS = {
    "dev": {"manifest": "dev-v1.json", "asset": "ifc-dev-v1.zip", "check": "sha256"},
    "expansion": {"manifest": "expansion-v1.json", "asset": "ifc-expansion-v1.zip", "check": "content_sha256"},
    "unseen": {"manifest": "unseen-v1.json", "asset": "ifc-unseen-v1.zip", "check": "sha256"},
    "grid": {"manifest": "grid-v1.json", "asset": "ifc-grid-v1.zip", "check": "sha256"},
}
GRID_SPLIT = "grid_evaluation"
# Deadline fraction alpha (of T_econ - T_fast above T_fast) x budget fraction beta (of the gap
# between the deadline-conditioned cost floor and the fast-anchor cost). The v1 QoS profiles are
# three of the 25 cells: tight = (1/100, 1/10), moderate = (1/4, 1/2), relaxed = (3/4, 9/10).
GRID_DEADLINE = (("001", 1, 100), ("005", 1, 20), ("025", 1, 4), ("050", 1, 2), ("075", 3, 4))
GRID_BUDGET = (("010", 1, 10), ("030", 3, 10), ("050", 1, 2), ("070", 7, 10), ("090", 9, 10))
UNSEEN_SPLIT = "unseen_evaluation"
RELEASE_TAG = "data"
FIXED_TIME = (2026, 9, 6, 0, 0, 0)  # deterministic zip member timestamps


def manifest(set_name: str = "dev") -> dict:
    return json.loads((ROOT / "manifests" / SETS[set_name]["manifest"]).read_text(encoding="utf-8"))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def expected_files(man: dict, check: str = "sha256") -> dict[str, str]:
    """path (relative to the dataset root) -> expected digest, for every instance and base file."""
    out = {e["path"]: e[check] for e in man["entries"]}
    out.update({b["path"]: b[check] for b in man["base_entries"]})
    return out


def digest(b: bytes, check: str) -> str:
    if check == "sha256":
        return sha(b)
    from generator.canonical import canonical_json_bytes  # needs the Dataset package on sys.path
    return sha(canonical_json_bytes(json.loads(b)))


# --------------------------------------------------------------------------- regen
def _groups(man: dict) -> list[tuple[str, list[dict]]]:
    by_base: dict[str, list[dict]] = {}
    for e in man["entries"]:
        by_base.setdefault(e["base_instance_id"], []).append(e)
    # largest workflows first so the greedy shard balance is even
    return sorted(by_base.items(), key=lambda kv: (-kv[1][0]["target_task_count"], kv[0]))


def shard_groups(man: dict, shards: int) -> list[list[tuple[str, list[dict]]]]:
    loads = [0.0] * shards
    out: list[list] = [[] for _ in range(shards)]
    for base_id, group in _groups(man):
        cost = group[0]["target_task_count"] ** 1.6
        i = min(range(shards), key=lambda k: loads[k])
        out[i].append((base_id, group))
        loads[i] += cost
    return out


def _selection_entries(a: argparse.Namespace, ds: Path, man: dict) -> dict[str, dict]:
    """Return candidate_id -> selection entry carrying the fields build_qos_instance needs."""
    if a.set == "dev":
        selection = json.loads((ds / "manifests" / "pilot-selection-v1.json").read_text(encoding="utf-8"))
        if selection["content_sha256"] != man["selection_sha256"]:
            raise SystemExit("pilot selection checksum does not match the manifest")
        return {s["candidate_id"]: s for s in selection["entries"]}
    # expansion: the manifest itself carries the frozen selection entries
    return {e["candidate_id"]: e for e in man["entries"]}


def cmd_regen(a: argparse.Namespace) -> int:
    ds = Path(a.dataset_repo).resolve()
    sys.path.insert(0, str(ds))
    from generator.config import load_config  # noqa: E402
    from generator.dax import normalize_dax  # noqa: E402
    from generator.instance import build_base_instance  # noqa: E402
    import generator.materialize as M  # noqa: E402

    man = manifest(a.set)
    check = SETS[a.set]["check"]
    head = subprocess.run(["git", "-C", str(ds), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head and head != man["generator_commit_sha"] and not a.allow_other_commit:
        print(f"Dataset checkout is {head}, manifest needs {man['generator_commit_sha']}", file=sys.stderr)
        return 2
    cfg = load_config(str(ds / "config" / "benchmark-v1.yaml"))
    if a.set == "unseen":
        return _regen_unseen(a, ds, man, cfg)
    if a.set == "grid":
        return _regen_grid(a, ds, man, cfg)
    sel = _selection_entries(a, ds, man)
    want = expected_files(man, check)
    out = Path(a.out)
    groups = shard_groups(man, a.shards)[a.shard]
    print(f"set {a.set}, shard {a.shard}/{a.shards}: {len(groups)} base instances, "
          f"{sum(len(g) for _, g in groups)} QoS instances, checked by {check}")
    bad = 0
    for base_id, group in groups:
        t0 = time.time()
        s0 = sel[group[0]["candidate_id"]]
        if s0["split"] not in ("development", "expansion_evaluation"):
            raise SystemExit("refusing to materialize a protected (holdout) entry")
        source = M._safe_source(ds / "source_workflows", s0["source_path"])
        if sha(source.read_bytes()) != s0["source_sha256"]:
            raise SystemExit(f"source workflow checksum mismatch for {s0['source_path']}")
        wf = normalize_dax(source, family=s0["family"], target_task_count=int(s0["target_task_count"]),
                           replicate_id=s0["replicate_id"], reference_mips=int(cfg["workflows"]["reference_mips"]))
        base = build_base_instance(wf, dict(cfg), scale=s0["resource_scale"],
                                   scenario=s0["scenario_profile"], seed=int(s0["ifc_realization_seed"]))
        if base["metadata"]["base_instance_id"] != base_id:
            raise SystemExit(f"base identity mismatch for {base_id}")
        cal = M.build_calibration_result(base, k=int(cfg["budget"]["calibration"]["tradeoff_solutions"]))
        files = {f"base/{base_id}.json": M._json_file_bytes(base)}
        for e in group:
            files[e["path"]] = M._json_file_bytes(M.build_qos_instance(sel[e["candidate_id"]], cal, cfg))
        mism = 0
        for rel, b in files.items():
            ok = digest(b, check) == want[rel]
            mism += not ok
            p = out / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
        bad += mism
        print(f"  {base_id}: {len(group)} QoS, {time.time() - t0:.1f}s, {'ok' if mism == 0 else f'{mism} MISMATCH'}",
              flush=True)
    if bad:
        print(f"{bad} regenerated files differ from the frozen hashes", file=sys.stderr)
        return 1
    return 0


def _unseen_model_check(ds: Path, man: dict) -> None:
    got = sha((ds / "config" / "benchmark-v1.yaml").read_bytes())
    if got != man["model_config_sha256"]:
        raise SystemExit("Dataset model configuration differs from the one frozen in the unseen manifest")
    src = json.loads((ds / "manifests" / "source-workflows-unseen-v1.json").read_text(encoding="utf-8"))
    if src["content_sha256"] != man["source_manifest_content_sha256"]:
        raise SystemExit("unseen source manifest differs from the frozen one")


def _write_group(out: Path, files: dict[str, bytes]) -> None:
    for rel, b in files.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)


def _regen_unseen(a: argparse.Namespace, ds: Path, man: dict, cfg: dict) -> int:
    from generator.unseen import build_group  # noqa: E402
    _unseen_model_check(ds, man)
    want = expected_files(man, "sha256")
    out = Path(a.out)
    groups = shard_groups(man, a.shards)[a.shard]
    print(f"set unseen, shard {a.shard}/{a.shards}: {len(groups)} base instances, "
          f"{sum(len(g) for _, g in groups)} QoS instances, checked by sha256")
    bad = 0
    for base_id, group in groups:
        if any(e["split"] != UNSEEN_SPLIT for e in group):
            raise SystemExit("refusing to materialize a non-unseen entry")
        t0 = time.time()
        files = build_group(ds / "source_workflows", group, cfg)
        mism = sum(sha(b) != want[rel] for rel, b in files.items())
        bad += mism
        _write_group(out, files)
        print(f"  {base_id}: {len(group)} QoS, {time.time() - t0:.1f}s, {'ok' if mism == 0 else f'{mism} MISMATCH'}",
              flush=True)
    if bad:
        print(f"{bad} regenerated files differ from the frozen hashes", file=sys.stderr)
        return 1
    return 0


# --------------------------------------------------------------------------- grid set (5 x 5 tightness)
def grid_config(cfg: dict) -> dict:
    """The unchanged v1 model with 25 extra QoS profiles d<alpha>-b<beta>."""
    import copy
    out = copy.deepcopy(cfg)
    for dt, dn, dd in GRID_DEADLINE:
        for bt, bn, bd in GRID_BUDGET:
            name = f"d{dt}-b{bt}"
            out["reference_makespan"]["deadline_interpolation_fractions"][name] = {"numerator": dn, "denominator": dd}
            out["budget"]["joint_qos_profiles"][name] = {"deadline_level": name,
                                                        "budget_gap_fraction": {"numerator": bn, "denominator": bd}}
    return out


def grid_entries(ds: Path, dev_manifest: dict) -> list[dict]:
    """159 development base realizations x 25 grid cells (never holdout bases)."""
    selection = json.loads((ds / "manifests" / "pilot-selection-v1.json").read_text(encoding="utf-8"))
    if selection["content_sha256"] != dev_manifest["selection_sha256"]:
        raise SystemExit("pilot selection checksum does not match the dev manifest")
    by_cid = {s["candidate_id"]: s for s in selection["entries"]}
    bases: dict[str, dict] = {}
    for e in dev_manifest["entries"]:
        s = by_cid[e["candidate_id"]]
        if s["split"] != "development":
            raise SystemExit("refusing to use a non-development base")
        bases.setdefault(e["base_instance_id"], s)
    out = []
    for base_id in sorted(bases):
        s = bases[base_id]
        for dt, dn, dd in GRID_DEADLINE:
            for bt, bn, bd in GRID_BUDGET:
                prof = f"d{dt}-b{bt}"
                cid = f"candidate-{base_id.removeprefix('base-')}-{prof}"
                out.append({
                    "candidate_id": cid, "instance_id": cid, "base_instance_id": base_id,
                    "family": s["family"], "target_task_count": int(s["target_task_count"]),
                    "replicate_id": s["replicate_id"], "source_path": s["source_path"],
                    "source_sha256": s["source_sha256"], "resource_scale": s["resource_scale"],
                    "scenario_profile": s["scenario_profile"], "ifc_realization_seed": int(s["ifc_realization_seed"]),
                    "qos_profile": prof, "deadline_fraction": f"{dn}/{dd}", "budget_fraction": f"{bn}/{bd}",
                    "split": GRID_SPLIT, "path": f"instances/grid/{cid}.json",
                })
    return out


def grid_build_group(ds: Path, cfg: dict, gcfg: dict, group: list[dict]) -> dict[str, bytes]:
    from generator.dax import normalize_dax  # noqa: E402
    from generator.instance import build_base_instance  # noqa: E402
    import generator.materialize as M  # noqa: E402
    s0 = group[0]
    source = M._safe_source(ds / "source_workflows", s0["source_path"])
    if sha(source.read_bytes()) != s0["source_sha256"]:
        raise SystemExit(f"source workflow checksum mismatch for {s0['source_path']}")
    wf = normalize_dax(source, family=s0["family"], target_task_count=int(s0["target_task_count"]),
                       replicate_id=s0["replicate_id"], reference_mips=int(cfg["workflows"]["reference_mips"]))
    base = build_base_instance(wf, dict(cfg), scale=s0["resource_scale"],
                               scenario=s0["scenario_profile"], seed=int(s0["ifc_realization_seed"]))
    if base["metadata"]["base_instance_id"] != s0["base_instance_id"]:
        raise SystemExit(f"base identity mismatch for {s0['base_instance_id']}")
    cal = M.build_calibration_result(base, k=int(cfg["budget"]["calibration"]["tradeoff_solutions"]))
    files = {f"base/{s0['base_instance_id']}.json": M._json_file_bytes(base)}
    for e in group:
        files[e["path"]] = M._json_file_bytes(M.build_qos_instance(e, cal, gcfg))
    return files


def _regen_grid(a: argparse.Namespace, ds: Path, man: dict, cfg: dict) -> int:
    gcfg = grid_config(cfg)
    want = expected_files(man, "sha256")
    out = Path(a.out)
    groups = shard_groups(man, a.shards)[a.shard]
    print(f"set grid, shard {a.shard}/{a.shards}: {len(groups)} base instances")
    bad = 0
    for base_id, group in groups:
        if any(e["split"] != GRID_SPLIT for e in group):
            raise SystemExit("refusing to materialize a non-grid entry")
        files = grid_build_group(ds, cfg, gcfg, group)
        mism = sum(sha(b) != want[rel] for rel, b in files.items())
        bad += mism
        _write_group(out, files)
        print(f"  {base_id}: {len(group)} QoS, {'ok' if mism == 0 else f'{mism} MISMATCH'}", flush=True)
    return 1 if bad else 0


def cmd_grid_build(a: argparse.Namespace) -> int:
    ds = Path(a.dataset_repo).resolve()
    sys.path.insert(0, str(ds))
    from generator.config import load_config  # noqa: E402
    if (ROOT / "manifests" / SETS["grid"]["manifest"]).exists():
        raise SystemExit("manifests/grid-v1.json already exists: the grid set is frozen; use regen")
    cfg = load_config(str(ds / "config" / "benchmark-v1.yaml"))
    gcfg = grid_config(cfg)
    entries = grid_entries(ds, manifest("dev"))
    groups = shard_groups({"entries": entries}, a.shards)[a.shard]
    out = Path(a.out)
    hashes: dict[str, dict] = {}
    for base_id, group in groups:
        t0 = time.time()
        files = grid_build_group(ds, cfg, gcfg, group)
        _write_group(out, files)
        for rel, b in files.items():
            hashes[rel] = {"sha256": sha(b), "content_sha256": digest(b, "content_sha256")}
        print(f"  {base_id}: {len(group)} QoS, {time.time() - t0:.1f}s", flush=True)
    (out / "hashes.json").write_text(json.dumps(hashes, sort_keys=True, indent=0) + "\n", encoding="utf-8")
    return 0


def cmd_grid_merge(a: argparse.Namespace) -> int:
    ds = Path(a.dataset_repo).resolve()
    sys.path.insert(0, str(ds))
    from generator.canonical import content_sha256  # noqa: E402
    target = ROOT / "manifests" / SETS["grid"]["manifest"]
    if target.exists():
        raise SystemExit("manifests/grid-v1.json already exists: refusing to overwrite a freeze")
    dev = manifest("dev")
    entries = grid_entries(ds, dev)
    hashes: dict[str, dict] = {}
    for f in sorted(glob.glob(a.inputs)):
        hashes.update(json.loads(Path(f).read_text(encoding="utf-8")))
    bases = sorted({e["base_instance_id"] for e in entries})
    dev_base = {b["path"]: b["sha256"] for b in dev["base_entries"]}
    missing = [e["path"] for e in entries if e["path"] not in hashes]
    missing += [f"base/{b}.json" for b in bases if f"base/{b}.json" not in hashes]
    if missing:
        raise SystemExit(f"{len(missing)} files missing from the shard hash lists")
    # the grid reuses the dev base realizations: their bytes must equal the frozen dev bases
    diff = [b for b in bases if hashes[f"base/{b}.json"]["sha256"] != dev_base[f"base/{b}.json"]]
    if diff:
        raise SystemExit(f"{len(diff)} rebuilt base files differ from the frozen dev bases")
    head = subprocess.run(["git", "-C", str(ds), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    man = {
        "schema_version": 1,
        "selection_id": "ifc-grid-v1",
        "scope": ("Deadline x budget tightness grid: the 159 development base realizations of the pilot, each "
                  "with 25 joint QoS cells (deadline fraction in {1/100,1/20,1/4,1/2,3/4} x budget fraction in "
                  "{1/10,3/10,1/2,7/10,9/10}), built with the unchanged v1 calibration. Holdout bases excluded. "
                  "Frozen before any scheduler ran on it."),
        "generator_commit_sha": head,
        "selection_sha256": dev["selection_sha256"],
        "deadline_fractions": [f"{n}/{d}" for _, n, d in GRID_DEADLINE],
        "budget_fractions": [f"{n}/{d}" for _, n, d in GRID_BUDGET],
        "instance_count": len(entries),
        "base_instance_count": len(bases),
        "split_counts": {GRID_SPLIT: len(entries)},
        "entries": [{**e, **hashes[e["path"]]} for e in entries],
        "base_entries": [{"base_instance_id": b, "path": f"base/{b}.json", **hashes[f"base/{b}.json"]} for b in bases],
    }
    man["content_sha256"] = content_sha256(man)
    target.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"froze {len(entries)} grid instances over {len(bases)} dev bases at Dataset {head}; "
          f"content_sha256 {man['content_sha256']}")
    return 0


# --------------------------------------------------------------------------- freeze (unseen only)
def cmd_freeze_build(a: argparse.Namespace) -> int:
    """Build one shard of the unseen set from the Dataset sources and record every file hash.

    Runs only while manifests/unseen-v1.json does not exist yet (the freeze happens once).
    """
    ds = Path(a.dataset_repo).resolve()
    sys.path.insert(0, str(ds))
    from generator.config import load_config  # noqa: E402
    from generator.unseen import build_group, enumerate_entries, load_unseen_config  # noqa: E402

    if (ROOT / "manifests" / SETS["unseen"]["manifest"]).exists():
        raise SystemExit("manifests/unseen-v1.json already exists: the unseen set is frozen; use regen")
    unseen = load_unseen_config(ds / "config" / "unseen-v1.yaml")
    cfg = load_config(str(ds / unseen["model_config"]))
    src = json.loads((ds / "manifests" / "source-workflows-unseen-v1.json").read_text(encoding="utf-8"))
    entries = enumerate_entries(unseen, cfg, src)
    groups = shard_groups({"entries": entries}, a.shards)[a.shard]
    out = Path(a.out)
    hashes: dict[str, dict] = {}
    print(f"freeze unseen shard {a.shard}/{a.shards}: {len(groups)} base instances")
    for base_id, group in groups:
        t0 = time.time()
        files = build_group(ds / "source_workflows", group, cfg)
        _write_group(out, files)
        for rel, b in files.items():
            hashes[rel] = {"sha256": sha(b), "content_sha256": digest(b, "content_sha256")}
        print(f"  {base_id}: {len(group)} QoS, {time.time() - t0:.1f}s", flush=True)
    (out / "hashes.json").write_text(json.dumps(hashes, sort_keys=True, indent=0) + "\n", encoding="utf-8")
    return 0


def cmd_freeze_merge(a: argparse.Namespace) -> int:
    """Write the frozen unseen manifest from all shard hash lists (one-time freeze)."""
    ds = Path(a.dataset_repo).resolve()
    sys.path.insert(0, str(ds))
    from generator.canonical import content_sha256  # noqa: E402
    from generator.config import load_config  # noqa: E402
    from generator.unseen import enumerate_entries, load_unseen_config  # noqa: E402

    target = ROOT / "manifests" / SETS["unseen"]["manifest"]
    if target.exists():
        raise SystemExit("manifests/unseen-v1.json already exists: refusing to overwrite a freeze")
    unseen = load_unseen_config(ds / "config" / "unseen-v1.yaml")
    cfg = load_config(str(ds / unseen["model_config"]))
    src_path = ds / "manifests" / "source-workflows-unseen-v1.json"
    src = json.loads(src_path.read_text(encoding="utf-8"))
    entries = enumerate_entries(unseen, cfg, src)
    hashes: dict[str, dict] = {}
    for f in sorted(glob.glob(a.inputs)):
        hashes.update(json.loads(Path(f).read_text(encoding="utf-8")))
    bases = sorted({e["base_instance_id"] for e in entries})
    missing = [e["path"] for e in entries if e["path"] not in hashes]
    missing += [f"base/{b}.json" for b in bases if f"base/{b}.json" not in hashes]
    if missing:
        print("\n".join(missing[:20]), file=sys.stderr)
        raise SystemExit(f"{len(missing)} files missing from the shard hash lists")
    head = subprocess.run(["git", "-C", str(ds), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    man = {
        "schema_version": 1,
        "selection_id": unseen["set_id"],
        "scope": ("Unseen source DAGs: 35 new Bharathi r04 replicates checksum-distinct from the frozen v1 "
                  "r01-r03, and 48 WfCommons/WfChef DAGs of four families absent from v1 (1000genome, "
                  "srasearch and blast at all seven sizes; soykb at 200/400/800, the sizes it can produce "
                  "exactly). Full factorial with 3 resource scales x 3 scenarios x 3 QoS profiles. "
                  "Frozen before any scheduler ran on it."),
        "generator_commit_sha": head,
        "model_config_sha256": sha((ds / unseen["model_config"]).read_bytes()),
        "unseen_config_sha256": sha((ds / "config" / "unseen-v1.yaml").read_bytes()),
        "source_manifest_content_sha256": src["content_sha256"],
        "source_count": src["artifact_count"],
        "instance_count": len(entries),
        "base_instance_count": len(bases),
        "split_counts": {UNSEEN_SPLIT: len(entries)},
        "hash_note": "sha256 = raw bytes; regeneration must be byte-identical. content_sha256 = sha256 of "
                     "generator.canonical.canonical_json_bytes(parsed JSON).",
        "entries": [{**e, **hashes[e["path"]]} for e in entries],
        "base_entries": [{"base_instance_id": b, "path": f"base/{b}.json", **hashes[f"base/{b}.json"]}
                         for b in bases],
    }
    man["content_sha256"] = content_sha256(man)
    target.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"froze {len(entries)} unseen instances over {len(bases)} bases from {src['artifact_count']} "
          f"sources at Dataset {head}; manifest content_sha256 {man['content_sha256']}")
    return 0


# --------------------------------------------------------------------------- pack / verify
def verify_tree(root: Path, set_name: str) -> list[str]:
    check = SETS[set_name]["check"]
    problems = []
    for rel, d in expected_files(manifest(set_name), check).items():
        p = root / rel
        if not p.exists():
            problems.append(f"missing {rel}")
        elif digest(p.read_bytes(), check) != d:
            problems.append(f"hash mismatch {rel}")
    return problems


def cmd_pack(a: argparse.Namespace) -> int:
    check = SETS[a.set]["check"]
    want = expected_files(manifest(a.set), check)
    found: dict[str, bytes] = {}
    for d in sorted(glob.glob(a.inputs)):
        for rel in want:
            p = Path(d) / rel
            if p.exists():
                found[rel] = p.read_bytes()
    problems = [f"missing {r}" for r in want if r not in found]
    problems += [f"hash mismatch {r}" for r, b in found.items() if digest(b, check) != want[r]]
    if problems:
        print("\n".join(problems[:20]), file=sys.stderr)
        return 1
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(zipfile.ZipInfo("manifest.json", FIXED_TIME),
                   (ROOT / "manifests" / SETS[a.set]["manifest"]).read_bytes(), zipfile.ZIP_DEFLATED)
        for rel in sorted(found):
            z.writestr(zipfile.ZipInfo(rel, FIXED_TIME), found[rel], zipfile.ZIP_DEFLATED)
    print(f"packed {len(found)} verified files -> {out} ({out.stat().st_size / 1e6:.1f} MB, sha256 {sha(out.read_bytes())})")
    return 0


def cmd_verify(a: argparse.Namespace) -> int:
    problems = verify_tree(Path(a.data), a.set)
    n = len(expected_files(manifest(a.set)))
    print("\n".join(problems[:20]) if problems else f"all {n} files of set {a.set} verified")
    return 1 if problems else 0


def cmd_fetch(a: argparse.Namespace) -> int:
    out = Path(a.out)
    if out.exists() and not verify_tree(out, a.set):
        print(f"{out} already holds the verified {a.set} dataset")
        return 0
    out.mkdir(parents=True, exist_ok=True)
    asset = SETS[a.set]["asset"]
    zpath = out.parent / asset
    if not zpath.exists():
        repo = a.repo or os.environ.get("GITHUB_REPOSITORY", "alphanum545/ifc-scheduling-benchmark")
        subprocess.run(["gh", "release", "download", RELEASE_TAG, "--repo", repo, "--pattern", asset,
                        "--dir", str(out.parent), "--clobber"], check=True)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(out)
    return cmd_verify(argparse.Namespace(data=str(out), set=a.set))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("regen")
    r.add_argument("--dataset-repo", required=True)
    r.add_argument("--shard", type=int, default=0)
    r.add_argument("--shards", type=int, default=1)
    r.add_argument("--out", required=True)
    r.add_argument("--allow-other-commit", action="store_true")
    k = sub.add_parser("pack")
    k.add_argument("--inputs", required=True)
    k.add_argument("--out", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--data", default="data/dev")
    f = sub.add_parser("fetch")
    f.add_argument("--out", default="data/dev")
    f.add_argument("--repo")
    fb = sub.add_parser("freeze-build")
    fb.add_argument("--dataset-repo", required=True)
    fb.add_argument("--shard", type=int, default=0)
    fb.add_argument("--shards", type=int, default=1)
    fb.add_argument("--out", required=True)
    fm = sub.add_parser("freeze-merge")
    fm.add_argument("--dataset-repo", required=True)
    fm.add_argument("--inputs", required=True, help="glob of shard hashes.json files")
    gb = sub.add_parser("grid-build")
    gb.add_argument("--dataset-repo", required=True)
    gb.add_argument("--shard", type=int, default=0)
    gb.add_argument("--shards", type=int, default=1)
    gb.add_argument("--out", required=True)
    gm = sub.add_parser("grid-merge")
    gm.add_argument("--dataset-repo", required=True)
    gm.add_argument("--inputs", required=True)
    for s in (r, k, v, f):
        s.add_argument("--set", choices=sorted(SETS), default="dev")
    a = p.parse_args()
    return {"regen": cmd_regen, "pack": cmd_pack, "verify": cmd_verify, "fetch": cmd_fetch,
            "freeze-build": cmd_freeze_build, "freeze-merge": cmd_freeze_merge,
            "grid-build": cmd_grid_build, "grid-merge": cmd_grid_merge}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
