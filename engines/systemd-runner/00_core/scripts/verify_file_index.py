#!/usr/bin/env python3
"""Verify FILE_INDEX_SHA256.txt integrity index (cross-platform).

Expected line format (sha256sum compatible):
    <sha256>  <relative/path>

Notes:
- Ignores empty lines and lines starting with '#'
- Paths are treated as relative to --root (default: repository root)
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_index_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    # Accept both "HASH  path" and "HASH *path" (sha256sum variants)
    parts = line.split()
    if len(parts) < 2:
        return None
    h = parts[0].strip()
    rel = " ".join(parts[1:]).strip()
    if rel.startswith("*"):
        rel = rel[1:]
    return h, rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Repository root used to resolve relative paths")
    ap.add_argument("--index", default="FILE_INDEX_SHA256.txt", help="Integrity index file")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    index_path = (root / args.index).resolve()

    if not index_path.exists():
        print(f"[ERR] index not found: {index_path}")
        return 2

    bad = 0
    missing = 0
    checked = 0

    for raw in index_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parsed = parse_index_line(raw)
        if parsed is None:
            continue
        expected_hash, rel = parsed
        target = (root / rel).resolve()
        checked += 1
        if not target.exists():
            missing += 1
            print(f"[MISS] {rel}")
            continue
        got = sha256_file(target)
        if got.lower() != expected_hash.lower():
            bad += 1
            print(f"[BAD]  {rel}")
            print(f"       expected={expected_hash}")
            print(f"       got     ={got}")

    ok = checked - bad - missing
    print(f"[SUMMARY] checked={checked} ok={ok} bad={bad} missing={missing}")
    return 0 if (bad == 0 and missing == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
