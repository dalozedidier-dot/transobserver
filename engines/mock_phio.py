#!/usr/bin/env python3
"""Mock PhiO: creates minimal phio_report.json and phio_manifest.json.

This is only to make the module runnable out of the box.
Replace with real PhiO calls when you plug the actual engine.
"""
import json, hashlib, datetime
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(p: Path, obj: dict) -> None:
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

def main(input_fixture: str, out_dir: str):
    inp = Path(input_fixture)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    report = {
        "engine": "PhiO-mock",
        "timestamp_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "input_fixture_sha256": sha256_file(inp),
        "coherence_score": None,
        "status": "ok"
    }
    write_json(out / "phio_report.json", report)

    manifest = {
        "engine": "PhiO-mock",
        "input": {"path": str(inp), "sha256": sha256_file(inp)},
        "artifacts": {"report": "phio_report.json"},
        "hashes": {"phio_report.json": sha256_file(out / "phio_report.json")}
    }
    write_json(out / "phio_manifest.json", manifest)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("Usage: mock_phio.py input/fixture.json out_dir")
    main(sys.argv[1], sys.argv[2])
