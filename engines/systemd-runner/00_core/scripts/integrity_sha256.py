#!/usr/bin/env python3
"""Deterministic SHA256 index generator.

Writes lines: <sha256>  <relative_path>

Excludes: .git, .github, __pycache__
"""

from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

EXCLUDE_DIRS = {".git", ".github", "__pycache__"}

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        yield p

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Repo root")
    ap.add_argument("--out", default="FILE_INDEX_SHA256.txt", help="Output filename")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    lines = []
    for p in iter_files(root):
        rel = p.relative_to(root).as_posix()
        lines.append(f"{sha256_file(p)}  {rel}")
    (root / args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
