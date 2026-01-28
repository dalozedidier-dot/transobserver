#!/usr/bin/env python3
"""Stable entrypoint for SystemD multisector harness.

Runs 01_tests_multisector/harness.py while keeping a stable top-level CLI.
"""

from __future__ import annotations

from pathlib import Path
import runpy
import sys

REPO_ROOT = Path(__file__).resolve().parent
TARGET = REPO_ROOT / "01_tests_multisector" / "harness.py"

if not TARGET.exists():
    raise SystemExit(f"Missing harness script: {TARGET}")

# Forward args; runpy will see __name__ == "__main__"
sys.argv[0] = str(TARGET)
runpy.run_path(str(TARGET), run_name="__main__")
