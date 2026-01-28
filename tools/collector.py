#!/usr/bin/env python3
import argparse, json, hashlib, datetime, shutil
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(p: Path, obj: dict) -> None:
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

def utc_cycle_id(now=None) -> str:
    now = now or datetime.datetime.utcnow().replace(microsecond=0)
    return now.strftime("%Y%m%d_%H%M%SZ")

def parse_sources(source_args):
    out = []
    for s in source_args:
        if ":" not in s:
            raise SystemExit(f"Invalid --source '{s}'. Expected logical_name:/path/to/file")
        name, path = s.split(":", 1)
        out.append((name.strip(), Path(path.strip())))
    return out

def collect_once(out_root: Path, sources, notes: str = ""):
    cycle_id = utc_cycle_id()
    out_dir = out_root / cycle_id
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    files = []
    for logical_name, src_path in sources:
        if not src_path.exists():
            raise SystemExit(f"Source file does not exist: {src_path}")
        dst = raw_dir / src_path.name
        shutil.copy2(src_path, dst)
        files.append({
            "name": logical_name,
            "filename": f"raw/{dst.name}",
            "sha256": sha256_file(dst),
            "bytes": dst.stat().st_size,
        })

    fixture = {
        "version": "1.0",
        "cycle_id": cycle_id,
        "timestamp_utc": cycle_id,
        "sources": files,
        "notes": notes or ""
    }

    fixture_path = out_dir / "fixture.json"
    write_json(fixture_path, fixture)

    fixture_sha = sha256_file(fixture_path)
    fixture["fixture_sha256"] = fixture_sha
    write_json(fixture_path, fixture)

    return out_dir

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shared_fixtures", help="Output root directory for fixtures")
    ap.add_argument("--source", action="append", default=[], help="logical_name:/path/to/file (repeatable)")
    ap.add_argument("--notes", default="", help="Optional notes for fixture.json")
    args = ap.parse_args()

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    sources = parse_sources(args.source)

    out_dir = collect_once(out_root, sources, notes=args.notes)
    print(str(out_dir))

if __name__ == "__main__":
    main()
