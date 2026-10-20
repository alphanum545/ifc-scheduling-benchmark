#!/usr/bin/env python3
"""Rebuild, verify, pack and fetch the 160-case IFC development dataset.

The public repository ships no instance files. The development split is regenerated
from the public Dataset repository (alphanum545/Dataset) at the generator commit
recorded in manifests/dev-v1.json, and every file is checked byte-for-byte against
the SHA-256 recorded in that manifest. The 40 protected holdout instances are never
generated: only development entries are listed in the manifest.

  python3 tools/data.py regen --dataset-repo ../Dataset --shard 0 --shards 20 --out .work/regen-0
  python3 tools/data.py pack  --inputs ".work/regen-*" --out .work/ifc-dev-v1.zip
  python3 tools/data.py fetch --out data            # download the release asset and verify
  python3 tools/data.py verify --data data          # re-check an extracted copy
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
MANIFEST = ROOT / "manifests" / "dev-v1.json"
ASSET = "ifc-dev-v1.zip"
RELEASE_TAG = "data"
FIXED_TIME = (2026, 9, 6, 0, 0, 0)  # deterministic zip member timestamps


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def expected_files(man: dict) -> dict[str, str]:
    """path (relative to the dataset root) -> sha256, for every instance and base file."""
    out = {e["path"]: e["sha256"] for e in man["entries"]}
    out.update({b["path"]: b["sha256"] for b in man["base_entries"]})
    return out


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


def cmd_regen(a: argparse.Namespace) -> int:
    ds = Path(a.dataset_repo).resolve()
    sys.path.insert(0, str(ds))
    from generator.config import load_config  # noqa: E402
    from generator.dax import normalize_dax  # noqa: E402
    from generator.instance import build_base_instance  # noqa: E402
    import generator.materialize as M  # noqa: E402

    man = manifest()
    head = subprocess.run(["git", "-C", str(ds), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head and head != man["generator_commit_sha"] and not a.allow_other_commit:
        print(f"Dataset checkout is {head}, manifest needs {man['generator_commit_sha']}", file=sys.stderr)
        return 2
    cfg = load_config(str(ds / "config" / "benchmark-v1.yaml"))
    selection = json.loads((ds / "manifests" / "pilot-selection-v1.json").read_text(encoding="utf-8"))
    if selection["content_sha256"] != man["selection_sha256"]:
        print("pilot selection checksum does not match the manifest", file=sys.stderr)
        return 2
    sel = {s["candidate_id"]: s for s in selection["entries"]}
    want = expected_files(man)
    out = Path(a.out)
    groups = shard_groups(man, a.shards)[a.shard]
    print(f"shard {a.shard}/{a.shards}: {len(groups)} base instances, {sum(len(g) for _, g in groups)} QoS instances")
    bad = 0
    for base_id, group in groups:
        t0 = time.time()
        s0 = sel[group[0]["candidate_id"]]
        if s0["split"] != "development":
            raise SystemExit("refusing to materialize a non-development entry")
        wf = normalize_dax(
            M._safe_source(ds / "source_workflows", s0["source_path"]),
            family=s0["family"], target_task_count=int(s0["target_task_count"]),
            replicate_id=s0["replicate_id"], reference_mips=int(cfg["workflows"]["reference_mips"]),
        )
        base = build_base_instance(wf, dict(cfg), scale=s0["resource_scale"],
                                   scenario=s0["scenario_profile"], seed=int(s0["ifc_realization_seed"]))
        if base["metadata"]["base_instance_id"] != base_id:
            raise SystemExit(f"base identity mismatch for {base_id}")
        cal = M.build_calibration_result(base, k=int(cfg["budget"]["calibration"]["tradeoff_solutions"]))
        files = {f"base/{base_id}.json": M._json_file_bytes(base)}
        for e in group:
            files[e["path"]] = M._json_file_bytes(M.build_qos_instance(sel[e["candidate_id"]], cal, cfg))
        for rel, b in files.items():
            ok = sha(b) == want[rel]
            bad += not ok
            p = out / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
        print(f"  {base_id}: {len(group)} QoS, {time.time() - t0:.1f}s, {'ok' if bad == 0 else 'MISMATCH'}")
    if bad:
        print(f"{bad} regenerated files differ from the frozen hashes", file=sys.stderr)
        return 1
    return 0


# --------------------------------------------------------------------------- pack / verify
def verify_tree(root: Path) -> list[str]:
    problems = []
    for rel, digest in expected_files(manifest()).items():
        p = root / rel
        if not p.exists():
            problems.append(f"missing {rel}")
        elif sha(p.read_bytes()) != digest:
            problems.append(f"hash mismatch {rel}")
    return problems


def cmd_pack(a: argparse.Namespace) -> int:
    want = expected_files(manifest())
    found: dict[str, bytes] = {}
    for d in sorted(glob.glob(a.inputs)):
        for rel in want:
            p = Path(d) / rel
            if p.exists():
                found[rel] = p.read_bytes()
    problems = [f"missing {r}" for r in want if r not in found]
    problems += [f"hash mismatch {r}" for r, b in found.items() if sha(b) != want[r]]
    if problems:
        print("\n".join(problems[:20]), file=sys.stderr)
        return 1
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        info = zipfile.ZipInfo("manifest.json", FIXED_TIME)
        z.writestr(info, MANIFEST.read_bytes(), zipfile.ZIP_DEFLATED)
        for rel in sorted(found):
            z.writestr(zipfile.ZipInfo(rel, FIXED_TIME), found[rel], zipfile.ZIP_DEFLATED)
    print(f"packed {len(found)} verified files -> {out} ({out.stat().st_size / 1e6:.1f} MB, sha256 {sha(out.read_bytes())})")
    return 0


def cmd_verify(a: argparse.Namespace) -> int:
    problems = verify_tree(Path(a.data))
    print("\n".join(problems[:20]) if problems else f"all {len(expected_files(manifest()))} files verified")
    return 1 if problems else 0


def cmd_fetch(a: argparse.Namespace) -> int:
    out = Path(a.out)
    if not verify_tree(out):
        print(f"{out} already holds the verified development dataset")
        return 0
    out.mkdir(parents=True, exist_ok=True)
    zpath = out.parent / ASSET
    if not zpath.exists():
        repo = a.repo or os.environ.get("GITHUB_REPOSITORY", "alphanum545/ifc-scheduling-benchmark")
        subprocess.run(["gh", "release", "download", RELEASE_TAG, "--repo", repo, "--pattern", ASSET,
                        "--dir", str(out.parent), "--clobber"], check=True)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(out)
    return cmd_verify(argparse.Namespace(data=str(out)))


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
    v.add_argument("--data", default="data")
    f = sub.add_parser("fetch")
    f.add_argument("--out", default="data")
    f.add_argument("--repo")
    a = p.parse_args()
    return {"regen": cmd_regen, "pack": cmd_pack, "verify": cmd_verify, "fetch": cmd_fetch}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
