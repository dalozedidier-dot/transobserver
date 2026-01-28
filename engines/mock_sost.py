#!/usr/bin/env python3
"""Mock SOST: copies example artifacts including run_manifest.json."""
import shutil
from pathlib import Path
import sys

def main(out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    example_run = Path(__file__).resolve().parents[1] / "examples" / "sost_ci" / "run1" / "run"
    # Keep the same internal structure as in example
    for rel in ["dd/dd_report.json", "ddr/ddr_report.json", "e/e_report.json", "run_manifest.json"]:
        src = example_run / rel
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: mock_sost.py out_dir")
    main(sys.argv[1])
