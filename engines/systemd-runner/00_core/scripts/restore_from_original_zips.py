#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restore full tree from 99_releases/original_zips (stdlib-only)

This script is designed for the failure mode:
- Git tree only contains root skeleton + original_zips
- But the complete bundle exists inside the zips.

It extracts all zips found in 99_releases/original_zips/ into repo root, without deleting existing files.

Usage:
  python 00_core/scripts/restore_from_original_zips.py --root . --dry-run
  python 00_core/scripts/restore_from_original_zips.py --root .

After extraction:
  - run verify_file_index.py
  - git add -A && git commit && git push
"""

from __future__ import annotations
import argparse
from pathlib import Path
import zipfile

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.', help='Repo root')
    ap.add_argument('--zips-dir', default='99_releases/original_zips', help='Directory containing source zips')
    ap.add_argument('--dry-run', action='store_true', help='List zip contents without extracting')
    args = ap.parse_args()

    root = Path(args.root).resolve()
    zips_dir = (root / args.zips_dir).resolve()
    if not zips_dir.exists():
        raise SystemExit(f"Missing zips dir: {zips_dir}")

    zips = sorted([p for p in zips_dir.glob('*.zip') if p.is_file()])
    if not zips:
        raise SystemExit(f"No .zip found in: {zips_dir}")

    for zpath in zips:
        print(f"ZIP: {zpath.name}")
        with zipfile.ZipFile(zpath) as z:
            names = z.namelist()
            if args.dry_run:
                for n in names[:50]:
                    print(f"  - {n}")
                if len(names) > 50:
                    print(f"  ... ({len(names)-50} more)")
            else:
                z.extractall(root)
                print(f"  extracted: {len(names)} entries")

    return 0

if __name__ == '__main__':
    raise SystemExit(main())
