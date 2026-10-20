#!/usr/bin/env python3
"""Rebuild, verify, pack and fetch the benchmark instance sets.

Two sets are defined, each by a manifest that lists every instance and base file with
its SHA-256:

  dev        manifests/dev-v1.json        160 development instances of the 200-input pilot
  expansion  manifests/expansion-v1.json  1,890 instances (630 new base configurations x 3 QoS)
                                           of the frozen ifc-expansion-selection-v1 cohort

The public repository ships no instance files. Each set is regenerated from the public
Dataset repository (alphanum545/Dataset) at the generator commit recorded in its manifest
and checked against the frozen hashes:
  dev        byte-identical files (sha256)
  expansion  identical content (content_sha256 = sha256 of generator.canonical.canonical_json_bytes),
             because the frozen expansion files were written with a different JSON layout
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
}
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
    for s in (r, k, v, f):
        s.add_argument("--set", choices=sorted(SETS), default="dev")
    a = p.parse_args()
    return {"regen": cmd_regen, "pack": cmd_pack, "verify": cmd_verify, "fetch": cmd_fetch}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
