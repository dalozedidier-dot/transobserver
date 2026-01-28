#!/usr/bin/env python3
"""PhiO wrapper for TransObserver cycles.

Runs contract_probe against input fixture and writes:
- phio_report.json (from contract_probe stdout if JSON else embedded)
- phio_manifest.json (hashes + pointers)

This wrapper avoids guessing a CLI. It directly calls the repo's contract_probe.py if present.
"""
import json, subprocess, sys, hashlib, datetime
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
    module_root = Path(__file__).resolve().parents[2]
    phio_repo = module_root / "engines" / "phio"
    probe = phio_repo / "contract_probe.py"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not probe.exists():
        raise SystemExit(f"PhiO contract_probe.py not found at {probe}")

    # Run probe
    proc = subprocess.run([sys.executable, str(probe), str(Path(input_fixture))],
                          capture_output=True, text=True, cwd=str(phio_repo))
    ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    report_path = out / "phio_report.json"
    # Try to parse stdout as JSON, otherwise store as structured envelope
    try:
        data = json.loads(proc.stdout.strip()) if proc.stdout.strip() else None
        if not isinstance(data, dict):
            raise ValueError("stdout not dict")
        data.setdefault("timestamp_utc", ts)
        data.setdefault("engine", "PhiO")
        data.setdefault("status", "ok" if proc.returncode == 0 else "failed")
        if proc.stderr:
            data.setdefault("stderr", proc.stderr[-8000:])
        write_json(report_path, data)
    except Exception:
        write_json(report_path, {
            "engine": "PhiO",
            "timestamp_utc": ts,
            "status": "ok" if proc.returncode == 0 else "failed",
            "stdout": proc.stdout[-8000:] if proc.stdout else "",
            "stderr": proc.stderr[-8000:] if proc.stderr else "",
        })

    manifest_path = out / "phio_manifest.json"
    manifest = {
        "run_id": "phio",
        "input": {"path": str(Path(input_fixture)), "sha256": sha256_file(Path(input_fixture))},
        "artifacts": {"report": report_path.name},
        "hashes": {report_path.name: sha256_file(report_path)},
    }
    write_json(manifest_path, manifest)

    if proc.returncode != 0:
        sys.exit(proc.returncode)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: phio_run.py input/fixture.json out_dir")
    main(sys.argv[1], sys.argv[2])
