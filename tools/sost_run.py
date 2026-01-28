#!/usr/bin/env python3
"""SOST wrapper for TransObserver cycles.

Calls engines/sost/scripts/run_sost.py with:
  --input <fixture.json> --out <out_dir>

Assumes SOST-Framework is self-contained.
"""
import subprocess, sys
from pathlib import Path

def main(input_fixture: str, out_dir: str):
    module_root = Path(__file__).resolve().parents[2]
    repo = module_root / "engines" / "sost"
    runner = repo / "scripts" / "run_sost.py"
    if not runner.exists():
        raise SystemExit(f"SOST runner not found at {runner}")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, str(runner), "--input", str(Path(input_fixture)), "--out", str(out)]
    # Use PYTHONPATH so sost/ package imports work
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(cmd, cwd=str(repo), env=env)
    sys.exit(proc.returncode)

if __name__ == "__main__":
    import os
    if len(sys.argv) != 3:
        raise SystemExit("Usage: sost_run.py input/fixture.json out_dir")
    main(sys.argv[1], sys.argv[2])
