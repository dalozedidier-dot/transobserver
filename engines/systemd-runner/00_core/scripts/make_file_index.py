#!/usr/bin/env python3
"""Generate FILE_INDEX_SHA256.txt (cross-platform).

- Walks the repository tree under --root
- Excludes VCS/CI folders by default
- Writes sha256sum-compatible lines: "<sha256>  <relative/path>"
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


DEFAULT_EXCLUDES = {
    ".git",
    ".github",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Repository root to index")
    ap.add_argument("--out", default="FILE_INDEX_SHA256.txt", help="Output index filename (relative to root)")
    ap.add_argument("--exclude", action="append", default=[], help="Extra directory or filename to exclude (repeatable)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_path = (root / args.out).resolve()
    excludes = set(DEFAULT_EXCLUDES) | set(args.exclude) | {out_path.name}

    lines = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        # exclude if any part matches
        if any(part in excludes for part in rel.parts):
            continue
        if p.is_file():
            h = sha256_file(p)
            lines.append(f"{h}  {rel.as_posix()}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote {len(lines)} lines -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
