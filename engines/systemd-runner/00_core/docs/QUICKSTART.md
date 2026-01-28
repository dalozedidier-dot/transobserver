QUICKSTART — Usage “en ligne”
============================

Note (clean bundle): if you downloaded the unified bundle, core scripts live under `00_core/`.


Option 1 — Google Colab (Python)
--------------------------------
1) Ouvrir un notebook Colab vide.
2) Charger ce dossier (zip) dans la session.
3) Dézipper (exemple dans une cellule) :

   !unzip -q SystemD_v0.3.1_clean.zip -d systemd

4) Déposer votre `TEST_MATRIX.md` dans `systemd/` (même niveau que README.md)
   ou ajuster le chemin en argument.

5) Exécuter :
   !python systemd/00_core/scripts/run_ddr.py --test-matrix systemd/00_core/TEST_MATRIX.md --out systemd/outputs

6) Lire :
   - systemd/outputs/ddr_report.json
   - systemd/outputs/extraction_report.json

Option 2 — Replit / Codespaces / autre runner Python
----------------------------------------------------
- Importer le dossier.
- Placer `TEST_MATRIX.md` à la racine.
- Lancer :
  python scripts/run_ddr.py --test-matrix TEST_MATRIX.md --out outputs

Conventions
-----------
- La spécification de référence est dans `specs/ddr_spec.yaml`.
- O-06 n’affecte que variance/std/entropie (moments) via min_n_for_moments=5.
- p90/p99 sont calculables dès n>=2 (min_n_for_quantiles=2).
- MAD calculable dès n>=2 (min_n_for_MAD=2).

