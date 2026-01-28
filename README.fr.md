# TransObserver module (harness unifié)

Ce dossier est un module autonome qui contient tout le nécessaire pour exécuter des cycles de bout en bout, sans dépendre des ZIP séparés.

Important: les moteurs réels PhiO, Systemd-runner et SOST ne sont pas inclus ici car les fichiers fournis étaient des artefacts CI, pas les dépôts complets. Pour que le module soit immédiatement exécutable, j’ai inclus un mode mock qui reproduit les outputs à partir des exemples fournis.

## Contenu
- `tools/collector.py` génère des fixtures synchronisées avec hash
- `tools/run_parallel.sh` exécute un cycle complet (mode mock par défaut)
- `tools/build_unified_manifest.py` produit `unified_manifest.json` qui hashe tout
- `tools/systemd_make_manifest.py` génère un `run_manifest.json` pour Systemd-runner
- `fixtures/prepared_bands/` contient les CSV de test
- `examples/` contient des sorties CI de référence
- `engines/` contient les mocks remplaçables par les vrais moteurs

## Démo rapide
1) Créer une fixture depuis un CSV fourni:
```bash
python tools/collector.py --out shared_fixtures --source band_imf:fixtures/prepared_bands/band_imf_colombia_log_nochange.csv
```

2) Lancer le cycle:
```bash
bash tools/run_parallel.sh shared_fixtures/<cycle_id> unified_cycles
```

Tu obtiens:
- `unified_cycles/<cycle_id>/unified_manifest.json`
- `phio/`, `systemd/`, `sost/` avec rapports et manifests

## Remplacement par les vrais moteurs
Dans `tools/run_parallel.sh`, remplace les appels aux mocks par tes commandes réelles:
- PhiO: contract_probe + notarize
- Systemd-runner: harness DDR/E
- SOST: run_sost.py ou équivalent

Ensuite, garde la même structure de sortie et les manifests.


## Mode réel (moteurs complets)
1) Place tes repos dans:
- `engines/phio`
- `engines/systemd-runner`
- `engines/sost`

2) Lance un cycle avec:
```bash
bash tools/run_parallel_real.sh shared_fixtures/<cycle_id> unified_cycles
```

Si l’autodétection échoue, ajoute tes commandes dans `config/engines.yaml` et adapte `tools/run_parallel_real.sh`.


## Intégration réelle incluse
Cette version embarque déjà:
- `engines/phio` (PhiO-main)
- `engines/sost` (SOST-Framework--main)

Donc tu peux lancer le mode réel immédiatement (PhiO + SOST), sans installer ces deux moteurs ailleurs.

Systemd-runner n’est pas inclus dans les fichiers fournis; tu peux déposer son dépôt dans `engines/systemd-runner` et le script tentera de l’exécuter.


## SystemD intégré
Cette version embarque aussi `engines/systemd-runner`.

Le wrapper `tools/systemd_run.py` exécute `00_core/scripts/run_ddr.py` avec `--with-e`.
Il cherche un fichier Markdown dans les sources du fixture (raw/*.md), en priorité `TEST_MATRIX.md`.
Si aucun Markdown n’est présent, SystemD écrit un `extraction_report.json` en statut `skipped` (cycle propre, pas d’échec).
