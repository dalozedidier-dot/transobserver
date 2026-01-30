#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run_capture(cmd: List[str]) -> Tuple[int, str]:
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout or ""


def ensure_gh() -> None:
    rc, out = run_capture(["gh", "--version"])
    if rc != 0:
        raise SystemExit("gh introuvable sur le runner.\n" + out)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@dataclass
class WorkflowSel:
    # Un sélecteur robuste pour gh workflow run
    # Priorité: id, puis file, puis name.
    id: Optional[int] = None
    file: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None


@dataclass
class RepoTarget:
    repo: str
    workflows: List[WorkflowSel]


def load_targets(path: Path) -> List[RepoTarget]:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: List[RepoTarget] = []
    for t in cfg.get("targets", []):
        repo = str(t["repo"])
        workflows: List[WorkflowSel] = []
        for w in t.get("workflows", []):
            workflows.append(
                WorkflowSel(
                    id=int(w["id"]) if "id" in w and w["id"] is not None else None,
                    file=w.get("file"),
                    name=w.get("name"),
                    label=w.get("label"),
                )
            )
        out.append(RepoTarget(repo=repo, workflows=workflows))
    return out


def selector(w: WorkflowSel) -> str:
    if w.id is not None:
        return str(w.id)
    if w.file:
        return str(w.file)
    if w.name:
        return str(w.name)
    raise ValueError("workflow selector missing: set id OR file OR name")


def gh_dispatch(owner: str, repo: str, w: WorkflowSel) -> Tuple[bool, str]:
    sel = selector(w)
    cmd = ["gh", "workflow", "run", sel, "-R", f"{owner}/{repo}"]
    rc, out = run_capture(cmd)
    return rc == 0, out.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Déclenche des workflows cross-repo (sans attendre la fin).")
    ap.add_argument("--owner", required=True, help="Owner GitHub (ex: dalozedidier-dot)")
    ap.add_argument("--targets", default="targets.yml", help="Fichier targets.yml")
    ap.add_argument("--out", default="_dispatch_out", help="Dossier de sortie")
    ap.add_argument("--keep-going", action="store_true", help="Continuer malgré les échecs")
    args = ap.parse_args()

    ensure_gh()

    targets_path = Path(args.targets).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = load_targets(targets_path)

    summary: Dict[str, Any] = {
        "utc_start": utc_now(),
        "owner": args.owner,
        "targets": str(targets_path),
        "results": [],
    }

    any_fail = False

    for rt in targets:
        for wf in rt.workflows:
            sel = selector(wf)
            label = wf.label or wf.name or wf.file or sel
            rec: Dict[str, Any] = {
                "repo": rt.repo,
                "workflow": label,
                "selector": sel,
                "ok": False,
                "output": None,
            }
            ok, out = gh_dispatch(args.owner, rt.repo, wf)
            rec["ok"] = bool(ok)
            rec["output"] = out
            summary["results"].append(rec)

            print(f"[{rt.repo}] {label} -> ok={ok}", flush=True)
            if not ok:
                any_fail = True
                if not args.keep_going:
                    summary["utc_end"] = utc_now()
                    write_json(out_dir / "summary.json", summary)
                    return 1

    summary["utc_end"] = utc_now()
    write_json(out_dir / "summary.json", summary)
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
