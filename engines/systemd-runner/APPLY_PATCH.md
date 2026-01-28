# Dossier correctif (patch)

Ce dossier contient uniquement les ajouts minimaux pour rendre le repo falsifiable sur GitHub (CI).

## Contenu
- `.github/workflows/ci.yml` : exécution CI (verify FILE_INDEX + core tests + harness).
- `.github/workflows/regen-expected.yml` : régénération manuelle des snapshots expected (workflow_dispatch).
- `00_core/scripts/verify_file_index.py` : vérification non-compensable de FILE_INDEX_SHA256.txt.
- `SXX_TEMPLATE_sector/` : template sectoriel minimal (README + profile + fixture).
- `01_tests_multisector/tests/expected/` : snapshots (issus de expected_updated.zip).

## Application
1) Copier ce dossier *au-dessus* de la racine du repo (merge), sans supprimer le contenu existant.
   - Les chemins doivent rester identiques.
2) Commit/push.

## Contrôle local (mêmes conditions que CI)
pip install -r requirements.txt
python 00_core/scripts/verify_file_index.py --root . --index FILE_INDEX_SHA256.txt
python 00_core/scripts/run_ddr.py --run-tests
python 01_tests_multisector/harness.py --repo-root 01_tests_multisector --profiles tests/profiles --out tests/results.json

## Remarque Principe S
Si `FILE_INDEX_SHA256.txt` ne référence pas ces nouveaux fichiers, la CI échouera (MISSING/MISMATCH).
Deux choix possibles :
- (A) étendre l'index pour inclure ces ajouts (puis régénérer l'index)
- (B) ne PAS vérifier l'index en CI (dégradation du contrat)
