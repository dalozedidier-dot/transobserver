#!/usr/bin/env python3
"""
tools/smoke_one.py

But:
- Exécuter un cycle complet sur un fichier d'entrée (CSV/JSON/etc) via tools/collector.py
  puis tools/run_parallel.sh (mock) ou tools/run_parallel_real.sh (real).
- Vérifier l'intégrité du unified_manifest.json (présence fichiers + sha256).
- Produire des logs exploitables en GitHub Actions (annotations ::error/::warning).
- La DERNIERE ligne imprimée sur stdout doit être uniquement le cycle_id (pour le workflow).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def gh_notice(msg: str) -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::notice::{msg}")
    else:
        print(msg)


def gh_warning(msg: str, file: str = "") -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        if file:
            print(f"::warning file={file}::{msg}")
        else:
            print(f"::warning::{msg}")
    else:
        print(f"WARNING: {msg}", file=sys.stderr)


def gh_error(msg: str, file: str = "") -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        if file:
            print(f"::error file={file}::{msg}")
        else:
            print(f"::error::{msg}")
    else:
        print(f"ERROR: {msg}", file=sys.stderr)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pick_latest_cycle_id(fixtures_root: Path) -> str:
    if not fixtures_root.exists():
        raise FileNotFoundError(f"fixtures folder not found: {fixtures_root}")
    dirs = [p for p in fixtures_root.iterdir() if p.is_dir()]
    if not dirs:
        raise FileNotFoundError(f"no cycle directory found under: {fixtures_root}")
    # Les noms de cycles sont typiquement triables lexicalement (YYYYMMDD_HHMMSSZ)
    return sorted(d.name for d in dirs)[-1]


def verify_unified_manifest(cycle_dir: Path) -> Dict[str, Any]:
    manifest_path = cycle_dir / "unified_manifest.json"
    if not manifest_path.exists():
        gh_error("unified_manifest.json manquant", file=str(manifest_path))
        raise SystemExit(2)

    m = load_json(manifest_path)

    artifacts: List[Dict[str, Any]] = m.get("artifacts") or []
    if not artifacts:
        gh_warning("unified_manifest.json ne contient pas de liste artifacts[] (rien à vérifier)")

    missing: List[str] = []
    bad_hash: List[str] = []

    for a in artifacts:
        rel = a.get("path")
        exp = a.get("sha256")
        if not rel or not exp:
            gh_warning(f"artifact entrée invalide (path/sha256 manquant): {a}")
            continue

        p = cycle_dir / rel
        if not p.exists():
            missing.append(rel)
            continue

        got = sha256_file(p)
        if got != exp:
            bad_hash.append(rel)
            gh_error(f"Hash mismatch pour {rel}: got={got} expected={exp}", file=rel)

    if missing:
        for rel in missing:
            gh_error("Fichier artefact manquant (référencé dans manifest)", file=rel)
        raise SystemExit(2)

    if bad_hash:
        raise SystemExit(2)

    return m


def run_checked(cmd: List[str], cwd: Path | None = None) -> None:
    try:
        subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)
    except subprocess.CalledProcessError as e:
        gh_error(f"Commande échouée (exit={e.returncode}): {' '.join(cmd)}")
        raise


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="Path under repo, ex: test_data/GDPDeflator.csv")
    ap.add_argument("--mode", choices=["mock", "real"], default="mock")
    ap.add_argument("--out-fixtures", default="shared_fixtures")
    ap.add_argument("--out-cycles", default="unified_cycles")
    ap.add_argument("--label", default="sample")
    args = ap.parse_args()

    in_path = Path(args.file)
    if not in_path.exists():
        gh_error("Fichier d'entrée introuvable", file=str(in_path))
        raise SystemExit(2)

    fixtures_root = Path(args.out_fixtures)
    cycles_root = Path(args.out_cycles)

    # 1) Collector -> crée un nouveau cycle fixtures_root/<cycle_id>/
    gh_notice(f"collector: {args.label}:{in_path}")
    run_checked(
        [
            "python3",
            "tools/collector.py",
            "--out",
            str(fixtures_root),
            "--source",
            f"{args.label}:{str(in_path)}",
        ]
    )

    # 2) Déterminer cycle_id
    cycle_id = pick_latest_cycle_id(fixtures_root)
    fixture_cycle_dir = fixtures_root / cycle_id

    # 3) Mode real: optionnellement produire un TEST_MATRIX.md depuis le CSV raw si helper disponible
    if args.mode == "real":
        csv_to_tm = Path("tools/csv_to_test_matrix.py")
        if csv_to_tm.exists() and in_path.suffix.lower() == ".csv":
            raw_csv = fixture_cycle_dir / "raw" / in_path.name
            tm_path = fixture_cycle_dir / "raw" / "TEST_MATRIX.md"
            if raw_csv.exists():
                gh_notice(f"real: build TEST_MATRIX from {raw_csv.name}")
                run_checked(
                    [
                        "python3",
                        str(csv_to_tm),
                        "--csv",
                        str(raw_csv),
                        "--out",
                        str(tm_path),
                    ]
                )
            else:
                gh_warning("real: raw CSV introuvable, TEST_MATRIX non généré", file=str(raw_csv))

    # 4) Run parallel
    cycles_root.mkdir(parents=True, exist_ok=True)
    if args.mode == "mock":
        runner = Path("tools/run_parallel.sh")
    else:
        runner = Path("tools/run_parallel_real.sh")

    if not runner.exists():
        gh_error("Runner introuvable", file=str(runner))
        raise SystemExit(2)

    gh_notice(f"run: {runner.name} {fixture_cycle_dir} {cycles_root}")
    run_checked(["bash", str(runner), str(fixture_cycle_dir), str(cycles_root)])

    cycle_dir = cycles_root / cycle_id
    if not cycle_dir.exists():
        gh_error("Cycle output introuvable après run", file=str(cycle_dir))
        raise SystemExit(2)

    # 5) Verify unified manifest
    started = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    gh_notice(f"verify: unified_manifest.json ({started})")
    m = verify_unified_manifest(cycle_dir)

    # 6) Logs structurés
    artifacts_count = len(m.get("artifacts") or [])
    gh_notice("SMOKE_TEST_SUCCESS")
    print(f"SMOKE_MODE={args.mode}")
    print(f"INPUT_FILE={in_path.as_posix()}")
    print(f"CYCLE_DIR={cycle_dir.as_posix()}")
    print(f"MANIFEST={ (cycle_dir / 'unified_manifest.json').as_posix() }")
    print(f"ARTIFACTS_COUNT={artifacts_count}")

    # Dernière ligne: cycle_id uniquement
    print(cycle_id)


if __name__ == "__main__":
    main()
