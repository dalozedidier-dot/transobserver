SystemD — core bundle (v0.3.1)
================================================

But
---
Fournir un dossier autonome pour :
1) extraire les sections d’un fichier `TEST_MATRIX.md`,
2) construire les séries proxy Pre/Post (IDs 1..n),
3) recalculer les invariants,
4) appliquer DD-R (et optionnellement E) avec règles de calculabilité / O-06 explicites.

Ce dossier ne suppose aucun état local préalable.

Structure
---------
- docs/      : référentiels (règles, frameworks, glossaire)
- specs/     : spécification DD-R (seuils, calculabilité, O-06)
- scripts/   : scripts d’extraction + calcul
- templates/ : modèle de TEST_MATRIX.md
- examples/  : exemples d’exécution et sorties

Entrée attendue
---------------
- Un fichier `TEST_MATRIX.md` contenant au minimum les sections :
  - "A — Tests structure" (ou équivalent) et
  - "B — Métrologie" (ou équivalent).
Le parseur accepte des variantes de titres (A/structure/tests ; B/métrologie/metrologie).

Sorties
-------
- `outputs/ddr_report.json` : invariants, divergences, classification DDR, statuts
- `outputs/extraction_report.json` : sections détectées, compte d’items, lignes non assignées
- (optionnel) `outputs/e_report.json` : compatibilité E sur invariants calculables

