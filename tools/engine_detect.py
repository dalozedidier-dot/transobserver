#!/usr/bin/env python3
"""Autodetect likely engine entrypoints inside local repos.

This script does NOT fetch repos. It only inspects directories under engines/.
It returns a JSON with resolved commands when possible.
"""
import json
from pathlib import Path

def exists_any(base: Path, rels):
    for r in rels:
        p = base / r
        if p.exists():
            return p
    return None

def detect_phio(path: Path):
    # candidates: run_all_tests.sh, validate_contract_warnings.sh, a python module, etc.
    sh = exists_any(path, ["run_all_tests.sh", "scripts/run_all_tests.sh"])
    if sh:
        return f"bash {sh.as_posix()}"
    return None

def detect_systemd(path: Path):
    # candidates: a cli module or a runner script
    py = exists_any(path, ["systemd_runner.py", "scripts/run_systemd_runner.py", "runner.py"])
    if py:
        return f"python3 {py.as_posix()}"
    # package module heuristic
    if (path / "pyproject.toml").exists() or (path / "setup.py").exists():
        # We can't know module name; leave None
        return None
    return None

def detect_sost(path: Path):
    py = exists_any(path, ["scripts/run_sost.py", "run_sost.py"])
    if py:
        return f"python3 {py.as_posix()}"
    return None

def main():
    engines_root = Path(__file__).resolve().parents[1] / "engines"
    out = {"phio": None, "systemd": None, "sost": None}

    phio = engines_root / "phio"
    systemd = engines_root / "systemd-runner"
    sost = engines_root / "sost"

    if phio.exists():
        out["phio"] = detect_phio(phio)
    if systemd.exists():
        out["systemd"] = detect_systemd(systemd)
    if sost.exists():
        out["sost"] = detect_sost(sost)

    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
