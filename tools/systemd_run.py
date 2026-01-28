#!/usr/bin/env python3
"""Systemd-runner wrapper for TransObserver cycles (v0.3.1 style).

Expected input:
- input_fixture: path to input/fixture.json (canonical)
Output:
- ddr_report.json (always when runnable)
- e_report.json (if computed; enabled here by default)
- extraction_report.json (minimal, also used when skipped)
- run_manifest.json (hashes + pointers)

This wrapper looks for a markdown TEST_MATRIX file in the fixture sources (raw/*.md).
If none is found, it produces a "skipped" extraction_report and manifest, then exits 0.
"""
import json, subprocess, sys, hashlib, datetime, os
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(p: Path, obj: dict) -> None:
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

def pick_test_matrix(fixture_path: Path) -> Path | None:
    try:
        fx = json.loads(fixture_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    base = fixture_path.parent
    # fixture.json uses filenames like raw/xxx.ext
    md_files = []
    for s in fx.get("sources", []):
        fn = s.get("filename") or ""
        if fn.lower().endswith(".md"):
            md_files.append(base / fn)
    # Prefer TEST_MATRIX.md if present
    for p in md_files:
        if p.name.upper() == "TEST_MATRIX.MD":
            return p if p.exists() else None
    # Otherwise first existing md
    for p in md_files:
        if p.exists():
            return p
    # Heuristic: scan raw/ for .md
    raw_dir = base / "raw"
    if raw_dir.exists():
        hits = sorted(raw_dir.glob("*.md"))
        if hits:
            return hits[0]
    return None

def main(input_fixture: str, out_dir: str):
    module_root = Path(__file__).resolve().parents[2]
    repo = module_root / "engines" / "systemd-runner"
    runner = repo / "00_core" / "scripts" / "run_ddr.py"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    fixture_path = Path(input_fixture)

    test_matrix = pick_test_matrix(fixture_path)
    extraction_path = out / "extraction_report.json"

    if not runner.exists():
        write_json(extraction_path, {
            "engine": "SystemD",
            "timestamp_utc": ts,
            "status": "failed",
            "reason": "missing_runner",
            "expected": str(runner),
        })
    elif test_matrix is None:
        write_json(extraction_path, {
            "engine": "SystemD",
            "timestamp_utc": ts,
            "status": "skipped",
            "reason": "no_markdown_test_matrix_in_fixture_sources",
            "hint": "Add a raw/*.md (preferably TEST_MATRIX.md) into fixture sources.",
        })
    else:
        # Run the core DDR runner with E computation
        cmd = [
            sys.executable, str(runner),
            "--test-matrix", str(test_matrix),
            "--out", str(out),
            "--with-e",
        ]
        proc = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True)
        write_json(extraction_path, {
            "engine": "SystemD",
            "timestamp_utc": ts,
            "status": "ok" if proc.returncode == 0 else "failed",
            "test_matrix": str(test_matrix),
            "stdout_tail": (proc.stdout or "")[-8000:],
            "stderr_tail": (proc.stderr or "")[-8000:],
            "returncode": proc.returncode,
        })

    # Build manifest
    artifacts = {}
    hashes = {}

    for name in ["ddr_report.json", "e_report.json", "extraction_report.json", "dd_report.json"]:
        p = out / name
        if p.exists():
            artifacts[name.replace("_report.json","").replace("ddr","ddr").replace("extraction","extraction")] = name
            hashes[name] = sha256_file(p)

    manifest = {
        "run_id": "systemd",
        "input": {"path": str(fixture_path), "sha256": sha256_file(fixture_path) if fixture_path.exists() else None},
        "artifacts": artifacts,
        "hashes": hashes,
    }
    write_json(out / "run_manifest.json", manifest)

    # Exit non-zero only if runner existed and test matrix existed and run failed
    if runner.exists() and test_matrix is not None:
        # read returncode from extraction report
        rc = json.loads(extraction_path.read_text(encoding="utf-8")).get("returncode", 0)
        if rc:
            sys.exit(int(rc))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: systemd_run.py input/fixture.json out_dir")
    main(sys.argv[1], sys.argv[2])
