#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System D — DD-R runner (v0.3.1-final)

Principes conservés (v0.3.0 → v0.3.1) :
- Parsing Markdown minimal (headings + list items) pour extraire les sections.
- Séries proxy = IDs séquentiels 1..n (n = nombre d'items de section).
- Invariants : mean, median, MAD, p90, p99.
- Divergence relative : div_rel = |post - pre| / |pre| (base pre).
- Décision par seuil eps ; classification DDR explicite.

Améliorations (v0.3.1) :
- Parsing plus robuste : ignore fenced code blocks, normalisation Unicode (accents), rapport de warnings.
- Mode strict : échec si taux de lignes non assignées dépasse un seuil.
- Calculs plus efficaces : tri unique réutilisé pour quantiles.
- UX : --verbose, résumé humain dans ddr_report.json.
- Tests intégrés : --run-tests (unittest, stdlib).

Aucune dépendance externe.
"""

import argparse
import json
import math
import os
import re
import statistics
import sys
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# -------------------------
# Normalisation texte
# -------------------------

def _norm_key(text: str) -> str:
    """Normalisation déterministe pour matching des headings/labels uniquement.

    Procédure (v0.3.1-final):
      1) NFC
      2) casefold
      3) NFKD
      4) suppression des caractères de catégorie Unicode 'Mn' (diacritiques)
      5) collapse des espaces multiples
      6) strip
    """
    text = unicodedata.normalize("NFC", text)
    text = text.casefold()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -------------------------
# Stats (déterministes)
# -------------------------

def _median_sorted(xs_sorted: List[float]) -> Optional[float]:
    n = len(xs_sorted)
    if n == 0:
        return None
    m = n // 2
    return xs_sorted[m] if n % 2 == 1 else (xs_sorted[m - 1] + xs_sorted[m]) / 2.0

def _median(xs: List[float]) -> Optional[float]:
    if not xs:
        return None
    xs_sorted = sorted(xs)
    return _median_sorted(xs_sorted)

def _mad(xs: List[float], min_n_for_MAD: int) -> Optional[float]:
    if len(xs) < min_n_for_MAD:
        return None
    xs_sorted = sorted(xs)
    med = _median_sorted(xs_sorted)
    if med is None:
        return None
    dev = [abs(x - med) for x in xs_sorted]
    dev_sorted = sorted(dev)
    return _median_sorted(dev_sorted)

def _q_linear_sorted(xs_sorted: List[float], q: float, min_n_for_quantiles: int) -> Optional[float]:
    n = len(xs_sorted)
    if n < min_n_for_quantiles:
        return None
    pos = (n - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(xs_sorted[lo])
    frac = pos - lo
    return float(xs_sorted[lo] + frac * (xs_sorted[hi] - xs_sorted[lo]))

def _div_rel(x: Optional[float], y: Optional[float]) -> Optional[float]:
    if x is None or y is None:
        return None
    if x == 0:
        return None
    return abs(y - x) / abs(x)

# -------------------------
# Parsing TEST_MATRIX.md
# -------------------------

SECTION_KEYS = ["rules_globales", "conventions_sorties", "A_structure", "B_metrologie"]

# Patterns sur titres normalisés (sans accents)
SECTION_PATTERNS = {
    "rules_globales": re.compile(r"regles\s+globales"),
    "conventions_sorties": re.compile(r"conventions\s+sorties"),
    "A_structure": re.compile(r"\ba\b.*(structure|tests?)"),
    "B_metrologie": re.compile(r"\bb\b.*(metrologie)"),
}

LIST_ITEM_RE = re.compile(r"^\s{0,3}(-|\*|\d+\.)\s+")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")

def _strip_fenced_code_blocks(lines: List[str]) -> Tuple[List[str], int]:
    """
    Supprime les blocs fenced (``` ou ~~~) pour éviter de compter des listes internes au code.
    Retourne (lignes_filtrees, nb_lignes_ignores).
    """
    out = []
    in_fence = False
    fence_token = None
    ignored = 0
    for ln in lines:
        m = FENCE_RE.match(ln)
        if m:
            tok = m.group(1)
            if not in_fence:
                in_fence = True
                fence_token = tok
            else:
                # fermer si même token
                if tok == fence_token:
                    in_fence = False
                    fence_token = None
            ignored += 1
            continue
        if in_fence:
            ignored += 1
            continue
        out.append(ln)
    return out, ignored

def parse_test_matrix(md_text: str) -> Tuple[Dict[str, List[str]], List[str], List[str], Dict]:
    lines = md_text.splitlines()
    lines, ignored_code = _strip_fenced_code_blocks(lines)

    items: Dict[str, List[str]] = {k: [] for k in SECTION_KEYS}
    unassigned: List[str] = []
    detected_sections: List[str] = []
    current: Optional[str] = None

    for ln in lines:
        # heading?
        if HEADING_RE.match(ln):
            title = HEADING_RE.sub("", ln).strip()
            title_n = _norm_key(title)
            current = None
            for k, rx in SECTION_PATTERNS.items():
                if rx.search(title_n):
                    current = k
                    detected_sections.append(k)
                    break
            continue

        # list item?
        if LIST_ITEM_RE.match(ln):
            if current in items:
                items[current].append(ln.strip())
            else:
                unassigned.append(ln.strip())

    meta = {
        "ignored_codeblock_lines": ignored_code,
        "total_lines": len(md_text.splitlines()),
        "total_lines_after_filter": len(lines),
    }
    return items, unassigned, detected_sections, meta

# -------------------------
# DD-R + E logic
# -------------------------

@dataclass
class Thresholds:
    eps: float = 0.02
    min_n_for_moments: int = 5  # périmètre O-06 : variance/std/entropie (non calculés ici)
    min_n_for_quantiles: int = 2
    min_n_for_MAD: int = 2

def compute_invariants(series: List[int], thr: Thresholds) -> Dict[str, Optional[float]]:
    xs = [float(v) for v in series]
    xs_sorted = sorted(xs)
    inv: Dict[str, Optional[float]] = {}
    inv["mean"] = statistics.mean(xs) if len(xs) >= 1 else None
    inv["median"] = _median_sorted(xs_sorted) if xs_sorted else None
    inv["MAD"] = _mad(xs, thr.min_n_for_MAD)
    inv["p90"] = _q_linear_sorted(xs_sorted, 0.90, thr.min_n_for_quantiles) if xs_sorted else None
    inv["p99"] = _q_linear_sorted(xs_sorted, 0.99, thr.min_n_for_quantiles) if xs_sorted else None

    # Moments (O-06): neutralisés si n < min_n_for_moments
    inv["variance"] = None
    inv["std"] = None
    inv["entropy"] = None  # réservé (non implémenté en v0.3.1-final)

    if len(xs) >= thr.min_n_for_moments and len(xs) >= 2:
        inv["variance"] = statistics.variance(xs)  # ddof=1
        inv["std"] = statistics.stdev(xs)          # ddof=1
    return inv

def ddr_compare(inv_pre: Dict[str, Optional[float]], inv_post: Dict[str, Optional[float]], thr: Thresholds) -> Dict:
    diffs: Dict[str, Optional[float]] = {}
    ok, ko, nc = [], [], []
    for k in ["mean", "median", "MAD", "p90", "p99"]:
        d = _div_rel(inv_pre.get(k), inv_post.get(k))
        diffs[k] = d
        if inv_pre.get(k) is None or inv_post.get(k) is None or d is None:
            nc.append(k)
        elif d > thr.eps:
            ko.append(k)
        else:
            ok.append(k)

    # Classification
    if nc:
        ddr = "INCONCLUSIF"
    elif (not ok) and ko:
        ddr = "ILLUSION"
    elif ok and ko:
        ddr = "PARTIAL"
    elif (not ko) and ok:
        ddr = "RESTORED"
    else:
        ddr = "INCONCLUSIF"

    return {"diffs": diffs, "invariants_ok": ok, "invariants_ko": ko, "invariants_nc": nc, "DDR": ddr}

def e_compatibility(inv_pre: Dict[str, Optional[float]], inv_post: Dict[str, Optional[float]], thr: Thresholds) -> Dict:
    ko = []
    nc = []
    for k in ["mean", "median", "MAD", "p90", "p99"]:
        d = _div_rel(inv_pre.get(k), inv_post.get(k))
        if inv_pre.get(k) is None or inv_post.get(k) is None or d is None:
            nc.append(k)
        elif d > thr.eps:
            ko.append(k)
    if ko:
        status = "INCOMPATIBLE"
    elif nc and not ko:
        status = "INCONCLUSIF"
    else:
        status = "COMPATIBLE"
    return {"E": status, "ko": ko, "nc": nc}

def _summary_human(ddr: Dict, thr: Thresholds) -> str:
    # Résumé non technique minimal, sans interprétation causale.
    nc = ddr["invariants_nc"]
    ko = ddr["invariants_ko"]
    ok = ddr["invariants_ok"]
    if nc:
        return f"Résultat inconclusif : invariants non calculables = {', '.join(nc)}."
    if ko:
        return f"Différences au-delà de eps={thr.eps}: KO={', '.join(ko)} ; OK={', '.join(ok) if ok else '∅'}."
    return f"Aucune divergence > eps={thr.eps} sur les invariants calculables."

# -------------------------
# Tests intégrés (stdlib)
# -------------------------

def _run_tests() -> int:
    import unittest

    class TestCore(unittest.TestCase):
        def test_quantile_linear(self):
            xs = [1.0,2.0,3.0,4.0]
            xs_s = sorted(xs)
            self.assertAlmostEqual(_q_linear_sorted(xs_s, 0.90, 2), 3.7, places=9)
            self.assertAlmostEqual(_q_linear_sorted(xs_s, 0.99, 2), 3.97, places=9)

        def test_mad(self):
            self.assertAlmostEqual(_mad([1,2,3,4], 2), 1.0, places=9)
            self.assertAlmostEqual(_mad([1,2,3], 2), 1.0, places=9)

        def test_parse_ignores_code(self):
            md = "# A tests structure\n- item1\n```\n- not_an_item\n```\n# B métrologie\n- item2\n"
            items, unassigned, detected, meta = parse_test_matrix(md)
            self.assertEqual(len(items["A_structure"]), 1)
            self.assertEqual(len(items["B_metrologie"]), 1)
            self.assertTrue(meta["ignored_codeblock_lines"] >= 2)

        def test_parse_unclosed_fence_ignores_rest(self):
            md = "# A tests structure\n- item1\n```\n- ignored\n# B metrologie\n- ignored2\n"
            items, unassigned, detected, meta = parse_test_matrix(md)
            # Everything after opening fence is ignored deterministically
            self.assertEqual(len(items["A_structure"]), 1)
            self.assertEqual(len(items["B_metrologie"]), 0)

        def test_heading_normalization_nfd(self):
            # "métrologie" with combining accent (NFD)
            title_nfd = "me\u0301trologie"
            self.assertEqual(_norm_key(title_nfd), "metrologie")
            md = f"# B {title_nfd}\n- item1\n"
            items, unassigned, detected, meta = parse_test_matrix(md)
            self.assertEqual(len(items["B_metrologie"]), 1)

        def test_div_rel_pre_zero_non_calculable(self):
            self.assertIsNone(_div_rel(0.0, 1.0))

        def test_mad_n1_non_calculable(self):
            self.assertIsNone(_mad([1.0], 2))

        def test_quantile_n2_linear(self):
            xs = [10.0, 20.0]
            xs_s = sorted(xs)
            # pos=(n-1)q; for q=0.90 pos=0.9 -> 10 + 0.9*(20-10)=19
            self.assertAlmostEqual(_q_linear_sorted(xs_s, 0.90, 2), 19.0, places=9)

        def test_neutralization_moments(self):
            thr = Thresholds(min_n_for_moments=5)
            inv = compute_invariants([1,2,3,4], thr)
            self.assertIsNone(inv["variance"])
            self.assertIsNone(inv["std"])


    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestCore)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    return 0 if res.wasSuccessful() else 1

# -------------------------
# Main
# -------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-matrix", required=False, help="Path to TEST_MATRIX.md")
    ap.add_argument("--out", default="outputs", help="Output directory")
    ap.add_argument("--eps", type=float, default=0.02)
    ap.add_argument("--min-n-moments", type=int, default=5)
    ap.add_argument("--min-n-quantiles", type=int, default=2)
    ap.add_argument("--min-n-mad", type=int, default=2)
    ap.add_argument("--with-e", action="store_true", help="Also compute E report")
    ap.add_argument("--verbose", action="store_true", help="Print key info to stdout")
    ap.add_argument("--strict-parsing", action="store_true", help="Fail immediately if any unassigned list item exists (exit code 2)")
    ap.add_argument("--max-unassigned-ratio", type=float, default=0.10, help="Fail if unassigned_ratio > X (exit code 2)")
    ap.add_argument("--run-tests", action="store_true", help="Run internal unit tests and exit")
    args = ap.parse_args(argv)

    if args.run_tests:
        return _run_tests()

    if not args.test_matrix:
        ap.error("--test-matrix is required unless --run-tests is used")

    thr = Thresholds(
        eps=args.eps,
        min_n_for_moments=args.min_n_moments,
        min_n_for_quantiles=args.min_n_quantiles,
        min_n_for_MAD=args.min_n_mad,
    )

    try:
        with open(args.test_matrix, "r", encoding="utf-8", errors="ignore") as f:
            md = f.read()
    except FileNotFoundError:
        print(f"ERROR: fichier introuvable: {args.test_matrix}", file=sys.stderr)
        return 3

    items, unassigned, detected, meta = parse_test_matrix(md)

    counts = {k: len(items[k]) for k in items}
    total_items = sum(counts.values())
    total_list_items = total_items + len(unassigned)
    unassigned_ratio = (len(unassigned) / total_list_items) if total_list_items > 0 else 0.0

    warnings: List[str] = []
    if "A_structure" not in detected:
        warnings.append("Section A_structure non détectée (pattern heading).")
    if "B_metrologie" not in detected:
        warnings.append("Section B_metrologie non détectée (pattern heading).")
    # Parsing rules (v0.3.1-final)
    # strict-parsing: stop immediately if any unassigned list item exists.
    if args.strict_parsing and len(unassigned) > 0:
        print(f"ERROR: strict-parsing: {len(unassigned)} item(s) de liste hors section valide.", file=sys.stderr)
        return 2

    # max-unassigned-ratio: stop if ratio exceeded (independent of strict-parsing).
    if unassigned_ratio > args.max_unassigned_ratio:
        print(f"ERROR: unassigned_ratio={unassigned_ratio:.3f} > {args.max_unassigned_ratio:.3f}", file=sys.stderr)
        return 2

    nA = len(items["A_structure"])
    nB = len(items["B_metrologie"])
    pre_ids = list(range(1, nA + 1))
    post_ids = list(range(1, nB + 1))

    inv_pre = compute_invariants(pre_ids, thr)
    inv_post = compute_invariants(post_ids, thr)
    ddr = ddr_compare(inv_pre, inv_post, thr)

    os.makedirs(args.out, exist_ok=True)

    extraction_report = {
        "version": "0.3.1-final",
        "detected_sections": detected,
        "counts": counts,
        "assigned_items_count": total_items,
        "total_list_items_count": total_list_items,
        "unassigned_items_count": len(unassigned),
        "unassigned_items_ratio": unassigned_ratio,
        "unassigned_items_preview": unassigned[:20],
        "warnings": warnings,
        "parsing_meta": meta,
        "note": "Les séries proxy sont IDs 1..n (n = nombre d'items listés dans la section).",
    }
    with open(os.path.join(args.out, "extraction_report.json"), "w", encoding="utf-8") as f:
        json.dump(extraction_report, f, ensure_ascii=False, indent=2)

    compat = "KO" if ddr["invariants_ko"] else ("INCONCLUSIF" if ddr["invariants_nc"] else "OK")
    neutralized = ["variance","std","entropy"] if (nA < thr.min_n_for_moments or nB < thr.min_n_for_moments) else []

    ddr_report = {
        "version": "0.3.1-final",
        "thresholds": thr.__dict__,
        "neutralized_by_min_n_for_moments": neutralized,
        "pre": {"section": "A_structure", "n": nA, "ids": pre_ids, "invariants": inv_pre},
        "post": {"section": "B_metrologie", "n": nB, "ids": post_ids, "invariants": inv_post},
        "diffs_rel": ddr["diffs"],
        "invariants_ok": ddr["invariants_ok"],
        "invariants_ko": ddr["invariants_ko"],
        "invariants_non_calculable": ddr["invariants_nc"],
        "DDR": ddr["DDR"],
        "status": {"execution": "OK", "compatibilite": compat},
        "summary_humain": {
            "resume": f"Comparaison A_structure (n={nA}) vs B_metrologie (n={nB}) : {len(ddr['invariants_ko'])} invariants KO, {len(ddr['invariants_ok'])} invariants OK. DDR={ddr['DDR']}.",
            "invariants_ok": ddr["invariants_ok"],
            "invariants_ko": ddr["invariants_ko"],
            "divergences_rel": ddr["diffs"],
            "neutralized": neutralized,
            "notes": [f"Quantiles calculés (min_n_for_quantiles={thr.min_n_for_quantiles})."]
        },
        "summary": _summary_human(ddr, thr),
        "limits": [
            "Phases proxy non temporelles.",
            "Matrice visible/tronquée => extraction potentiellement partielle.",
            "O-06 (moments) : variance/std/entropie neutralisés si n<min_n_for_moments (non calculés ici).",
        ],
    }
    with open(os.path.join(args.out, "ddr_report.json"), "w", encoding="utf-8") as f:
        json.dump(ddr_report, f, ensure_ascii=False, indent=2)

    if args.with_e:
        e_rep = e_compatibility(inv_pre, inv_post, thr)
        with open(os.path.join(args.out, "e_report.json"), "w", encoding="utf-8") as f:
            json.dump(e_rep, f, ensure_ascii=False, indent=2)

    if args.verbose:
        print(ddr_report["summary"])
        if warnings:
            print("WARNINGS:", "; ".join(warnings))

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
