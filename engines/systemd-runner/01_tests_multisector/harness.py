#!/usr/bin/env python3
# SystemD multisector test harness v0.1
# - Profiles (YAML) = contract: ingestion + adapter_id + params + pre/post selectors
# - Mode supported here: STRUCT_N (proxies 1..n)
# - Outputs: schema short {ok,ko,nc,ddr,e,div_rel,meta} + extraction + hash
from __future__ import annotations

import argparse, csv, hashlib, json, math, os, re, statistics, unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# ---------------------------
# Path resolution
# ---------------------------
def resolve_rel(repo_root: Path, rel: str) -> Path:
    """Resolve a repo-relative path.
    Compatibility rule:
    - If rel starts with 'tests/', prefer '01_tests_multisector/tests/' under repo_root.
    - Otherwise try repo_root/rel, then fallback to repo_root/'01_tests_multisector'/rel.
    """
    rel = rel.replace("\\", "/")
    primary = (repo_root / rel)
    if rel.startswith("tests/"):
        alt = (repo_root / "01_tests_multisector" / rel)
        if alt.exists():
            return alt
    if primary.exists():
        return primary
    alt2 = (repo_root / "01_tests_multisector" / rel)
    return alt2 if alt2.exists() else primary


# ---------------------------
# Kernel (STRUCT_N): proxies 1..n
# ---------------------------

def median(xs_sorted: List[float]) -> Optional[float]:
    if not xs_sorted:
        return None
    n = len(xs_sorted)
    m = n // 2
    return xs_sorted[m] if n % 2 == 1 else (xs_sorted[m-1] + xs_sorted[m]) / 2.0

def mad(xs_sorted: List[float], min_n_for_MAD: int) -> Optional[float]:
    if len(xs_sorted) < min_n_for_MAD:
        return None
    med = median(xs_sorted)
    if med is None:
        return None
    dev = sorted([abs(x - med) for x in xs_sorted])
    return median(dev)

def q_linear(xs_sorted: List[float], q: float, min_n_for_quantiles: int) -> Optional[float]:
    if len(xs_sorted) < min_n_for_quantiles:
        return None
    n = len(xs_sorted)
    pos = (n - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs_sorted[lo]
    frac = pos - lo
    return xs_sorted[lo] + frac * (xs_sorted[hi] - xs_sorted[lo])

def div_rel(pre: Optional[float], post: Optional[float]) -> Optional[float]:
    if pre is None or post is None:
        return None
    if pre == 0:
        return None
    return abs(post - pre) / abs(pre)

@dataclass
class Thresholds:
    eps: float = 0.02
    min_n_for_moments: int = 5
    min_n_for_quantiles: int = 2
    min_n_for_MAD: int = 2

def compute_invariants(ids: List[int], th: Thresholds) -> Dict[str, Optional[float]]:
    xs = [float(x) for x in ids]
    xs_sorted = sorted(xs)
    out: Dict[str, Optional[float]] = {
        "mean": statistics.mean(xs) if xs else None,
        "median": median(xs_sorted),
        "MAD": mad(xs_sorted, th.min_n_for_MAD),
        "p90": q_linear(xs_sorted, 0.90, th.min_n_for_quantiles),
        "p99": q_linear(xs_sorted, 0.99, th.min_n_for_quantiles),
    }
    return out

def classify_ddr(ok: List[str], ko: List[str], nc: List[str]) -> str:
    if nc:
        return "INCONCLUSIF"
    if not ok and ko:
        return "ILLUSION"
    if ok and ko:
        return "PARTIAL"
    if not ko:
        return "RESTORED"
    return "INCONCLUSIF"

def compute_ddr_short(pre_n: int, post_n: int, th: Thresholds) -> Dict[str, Any]:
    pre_ids = list(range(1, pre_n + 1))
    post_ids = list(range(1, post_n + 1))
    pre_inv = compute_invariants(pre_ids, th)
    post_inv = compute_invariants(post_ids, th)

    diffs: Dict[str, Optional[float]] = {}
    ok: List[str] = []
    ko: List[str] = []
    nc: List[str] = []

    for k in ["mean", "median", "MAD", "p90", "p99"]:
        d = div_rel(pre_inv.get(k), post_inv.get(k))
        diffs[k] = d
        if d is None:
            nc.append(k)
        elif d > th.eps:  # strict
            ko.append(k)
        else:
            ok.append(k)

    ok.sort(); ko.sort(); nc.sort()
    ddr = classify_ddr(ok, ko, nc)
    e = "INCONCLUSIF" if nc else ("INCOMPATIBLE" if ko else "COMPATIBLE")

    return {"ok": ok, "ko": ko, "nc": nc, "ddr": ddr, "e": e, "div_rel": diffs}

def canonical_json_bytes(obj: Any) -> bytes:
    # Stable representation for hashing
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return s.encode("utf-8")

def sha256_hex(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()

# ---------------------------
# Adapters (ingestion -> counts)
# ---------------------------

def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

LIST_ITEM_RX = re.compile(r"^\s{0,3}(-|\*|\d+\.)\s+")
HEADING_RX = re.compile(r"^\s{0,3}#{1,6}\s+")
FENCED_START = re.compile(r"^\s{0,3}(`{3,}|~{3,})")

DOCS_TARGETS = {
    "rules_globales": re.compile(r"r[eè]gles\s+globales", re.I),
    "conventions_sorties": re.compile(r"conventions\s+sorties", re.I),
    "A_structure": re.compile(r"(?:^|\b)A(?:\b|[^a-zA-Z]).*(structure|tests?)|(tests?\s+structure)", re.I),
    "B_metrologie": re.compile(r"(?:^|\b)B(?:\b|[^a-zA-Z]).*(m[eé]trologie)|(m[eé]trologie)", re.I),
}

SECTION_KEYS = ["rules_globales", "conventions_sorties", "A_structure", "B_metrologie"]

def adapter_docs(md_text: str, break_on_blank: bool = True) -> Tuple[Dict[str,int], List[str]]:
    items = {k: 0 for k in SECTION_KEYS}
    unassigned: List[str] = []
    current: Optional[str] = None
    in_fence = False
    fence = None

    for raw in md_text.splitlines():
        line = raw.rstrip("\n")
        if break_on_blank and (not in_fence) and line.strip() == "":
            current = None
            continue

        if in_fence:
            if fence and re.match(r"^\s{0,3}"+re.escape(fence)+r"$", line.strip()):
                in_fence = False
                fence = None
            continue

        m = FENCED_START.match(line)
        if m:
            in_fence = True
            fence = m.group(1)
            continue

        if HEADING_RX.match(line):
            title = HEADING_RX.sub("", line).strip()
            ntitle = normalize_unicode(title)
            current = None
            for k, rx in DOCS_TARGETS.items():
                if rx.search(ntitle):
                    current = k
                    break
            continue

        if LIST_ITEM_RX.match(line):
            if current in items:
                items[current] += 1
            else:
                unassigned.append(line.strip())

    return items, unassigned

def adapter_tickets_csv(csv_path: Path, group_col: str) -> Dict[str,int]:
    counts: Dict[str,int] = {}
    with csv_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row.get(group_col) or "").strip()
            if key == "":
                key = "__UNASSIGNED__"
            counts[key] = counts.get(key, 0) + 1
    return counts

def adapter_generic_json(json_path: Path) -> Dict[str,int]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    # Accept either {"groups": {"A": 51, "B": 50}} or {"rows":[{"group":"A"},...], "group_col":"group"}
    if isinstance(data, dict) and "groups" in data and isinstance(data["groups"], dict):
        return {str(k): int(v) for k,v in data["groups"].items()}
    rows = data.get("rows", [])
    group_col = data.get("group_col", "group")
    counts: Dict[str,int] = {}
    for r in rows:
        key = str(r.get(group_col, "__UNASSIGNED__"))
        counts[key] = counts.get(key, 0) + 1
    return counts

# ---------------------------
# Harness execution
# ---------------------------

def run_case(profile: Dict[str,Any], repo_root: Path, update_expected: bool) -> Dict[str,Any]:
    mode = profile["mode"]
    if mode != "STRUCT_N":
        raise ValueError(f"Unsupported mode in this harness: {mode}")

    ingestion = profile["ingestion"]
    adapter_id = profile["adapter_id"]
    th = Thresholds(
        eps=float(profile.get("eps", 0.02)),
        min_n_for_moments=int(profile.get("min_n_for_moments", 5)),
        min_n_for_quantiles=int(profile.get("min_n_for_quantiles", 2)),
        min_n_for_MAD=int(profile.get("min_n_for_MAD", 2)),
    )

    fixture_path = resolve_rel(repo_root, profile["fixture"])
    strict = bool(profile.get("strict_parsing", False))
    max_unassigned_ratio = float(profile.get("max_unassigned_ratio", 0.1))

    # Extract counts
    unassigned_count = 0
    items_count: Dict[str,int] = {}
    if adapter_id == "docs":
        md = fixture_path.read_text(encoding="utf-8", errors="ignore")
        items_count, unassigned = adapter_docs(md, break_on_blank=True)
        unassigned_count = len(unassigned)
    elif adapter_id == "tickets":
        group_col = profile.get("group_col", "Status")
        items_count = adapter_tickets_csv(fixture_path, group_col=group_col)
        unassigned_count = items_count.get("__UNASSIGNED__", 0)
    elif adapter_id == "generic":
        items_count = adapter_generic_json(fixture_path)
        unassigned_count = items_count.get("__UNASSIGNED__", 0)
    else:
        raise ValueError(f"Unknown adapter_id: {adapter_id}")

    total = sum(items_count.values())
    unassigned_ratio = (unassigned_count / total) if total > 0 else 0.0
    if strict and unassigned_count > 0:
        raise ValueError("Strict parsing failed: unassigned items found")
    if unassigned_ratio > max_unassigned_ratio:
        # warning only here; profiles may choose strict if needed
        pass

    pre_key = profile["pre_key"]
    post_key = profile["post_key"]
    pre_n = int(items_count.get(pre_key, 0))
    post_n = int(items_count.get(post_key, 0))

    ddr = compute_ddr_short(pre_n, post_n, th)

    report = {
        "meta": {
            "profile_id": profile["id"],
            "mode": mode,
            "ingestion": ingestion,
            "adapter_id": adapter_id,
            "kernel": "STRUCT_N_v0.1",
            "eps": th.eps,
            "min_n_for_moments": th.min_n_for_moments,
            "min_n_for_quantiles": th.min_n_for_quantiles,
            "min_n_for_MAD": th.min_n_for_MAD,
        },
        "extraction": {
            "fixture": str(profile["fixture"]),
            "items_count": items_count,
            "unassigned_items_count": unassigned_count,
            "unassigned_ratio": round(unassigned_ratio, 6),
            "pre_key": pre_key,
            "post_key": post_key,
            "pre_n": pre_n,
            "post_n": post_n,
        },
        "ddr": ddr,
    }

    report["hash_sha256"] = sha256_hex(report)

    expected_rel = profile.get("expected")
    if expected_rel:
        expected_path = resolve_rel(repo_root, expected_rel)
        hash_path = expected_path.with_suffix(".sha256.txt")

        if update_expected:
            expected_path.parent.mkdir(parents=True, exist_ok=True)
            expected_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
            hash_path.write_text(report["hash_sha256"]+"\n", encoding="utf-8")
            status = "UPDATED"
        else:
            if not expected_path.exists() or not hash_path.exists():
                status = "MISSING_EXPECTED"
            else:
                exp = json.loads(expected_path.read_text(encoding="utf-8"))
                exp_hash = hash_path.read_text(encoding="utf-8").strip()
                status = "PASS" if (exp_hash == report["hash_sha256"]) else "FAIL_HASH"
        report["expected_status"] = status

    return report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".", help="Repo root containing tests/")
    ap.add_argument("--profiles", default="01_tests_multisector/tests/profiles", help="Directory with profile YAMLs")
    ap.add_argument("--update-expected", action="store_true", help="Write expected snapshots")
    ap.add_argument("--out", default="01_tests_multisector/tests/results.json", help="Aggregated results JSON")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    profiles_dir = resolve_rel(repo_root, args.profiles).resolve()

    results: List[Dict[str,Any]] = []
    for p in sorted(profiles_dir.glob("*.yaml")):
        profile = yaml.safe_load(p.read_text(encoding="utf-8"))
        results.append(run_case(profile, repo_root, update_expected=args.update_expected))

    out_path = resolve_rel(repo_root, args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    # human summary
    summary = {}
    for r in results:
        sid = r["meta"]["profile_id"]
        summary[sid] = r.get("expected_status","OK")
    print(json.dumps(dict(sorted(summary.items())), ensure_ascii=False, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
