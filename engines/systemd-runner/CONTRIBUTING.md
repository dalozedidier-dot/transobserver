# CONTRIBUTING

Ce dépôt est contractuel : les profils YAML et les expected snapshots définissent des invariants.

## Règles de contribution (structure)
1. Toute modification de comportement doit être accompagnée :
   - d’une mise à jour des expected snapshots via `--update-expected`,
   - d’une justification courte (commit message + note dans `REPAIR_NOTES.md` ou équivalent si présent).
2. Toute modification de fichiers versionnés listés dans `FILE_INDEX_SHA256.txt` implique :
   - régénération de l’index,
   - commit de l’index mis à jour.

## Tests
- Core self-tests :
  `python 00_core/scripts/run_ddr.py --run-tests`
- Harness :
  `python 01_tests_multisector/harness.py --repo-root .`

