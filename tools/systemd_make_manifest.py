#!/usr/bin/env python3
import argparse, json, hashlib
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(p: Path, obj: dict) -> None:
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to input/fixture.json")
    ap.add_argument("--out", required=True, help="Systemd-runner output directory")
    ap.add_argument("--run-id", default="systemd", help="run_id field")
    args = ap.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = [
        ("ddr", out_dir / "ddr_report.json"),
        ("e", out_dir / "e_report.json"),
        ("extraction", out_dir / "extraction_report.json"),
        ("dd", out_dir / "dd_report.json"),
    ]

    artifacts = {}
    hashes = {}

    for key, p in candidates:
        if p.exists():
            rel = p.relative_to(out_dir).as_posix()
            if key == "ddr":
                artifacts["ddr"] = rel
            elif key == "e":
                artifacts["e"] = rel
            elif key == "dd":
                artifacts["dd"] = rel
            else:
                artifacts["extraction"] = rel
            hashes[p.name] = sha256_file(p)

    manifest = {
        "run_id": args.run_id,
        "input": {
            "path": str(input_path),
            "sha256": sha256_file(input_path),
        },
        "artifacts": artifacts,
        "hashes": hashes,
    }

    write_json(out_dir / "run_manifest.json", manifest)
    print(str(out_dir / "run_manifest.json"))

if __name__ == "__main__":
    main()
