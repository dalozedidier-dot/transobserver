#!/usr/bin/env python3
"""Mock Systemd-runner: copies example artifacts, then emits run_manifest.json."""
import shutil
from pathlib import Path
import subprocess, sys

def main(input_fixture: str, out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Copy included CI example outputs
    example_dir = Path(__file__).resolve().parents[1] / "examples" / "systemd_ci" / "ddr_smoke"
    for name in ["ddr_report.json", "e_report.json", "extraction_report.json"]:
        src = example_dir / name
        if src.exists():
            shutil.copy2(src, out / name)

    # Create manifest using shared helper
    tools_dir = Path(__file__).resolve().parents[1] / "tools"
    subprocess.check_call([sys.executable, str(tools_dir / "systemd_make_manifest.py"), "--input", input_fixture, "--out", str(out)])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: mock_systemd.py input/fixture.json out_dir")
    main(sys.argv[1], sys.argv[2])
