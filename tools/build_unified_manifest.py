#!/usr/bin/env python3
import json, hashlib, sys
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def walk_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file():
            yield p

def main(cycle_dir: str):
    root = Path(cycle_dir)
    input_fixture = root / "input" / "fixture.json"

    manifest = {
        "version": "1.0",
        "cycle_id": root.name,
        "input": {
            "fixture_path": "input/fixture.json",
            "fixture_sha256": sha256_file(input_fixture) if input_fixture.exists() else None,
        },
        "artifacts": [],
    }

    for p in walk_files(root):
        rel = p.relative_to(root).as_posix()
        if rel.endswith("unified_manifest.json"):
            continue
        manifest["artifacts"].append({
            "path": rel,
            "sha256": sha256_file(p),
            "bytes": p.stat().st_size,
        })

    print(json.dumps(manifest, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build_unified_manifest.py unified_cycles/<cycle_id>")
    main(sys.argv[1])
