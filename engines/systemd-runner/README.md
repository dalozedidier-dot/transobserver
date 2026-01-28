# SystemD — DD-R Runner & Multisector Harness (v0.3.1)

Runner + harness contractuel pour **analyse descriptive** (frameworks DD / DD‑R / E) :
- **00_core** : runner DD‑R (stdlib-only) + specs + templates.
- **01_tests_multisector** : harness de tests multi‑secteurs (profils YAML → fixtures → expected snapshots).

[![tests (ci.yml)](https://github.com/dalozedidier-dot/Systemd-runner/actions/workflows/ci.yml/badge.svg?branch=main&event=push&label=tests)](https://github.com/dalozedidier-dot/Systemd-runner/actions/workflows/ci.yml)
[![tests (python-app.yml)](https://github.com/dalozedidier-dot/Systemd-runner/actions/workflows/python-app.yml/badge.svg?branch=main&event=push&label=tests)](https://github.com/dalozedidier-dot/Systemd-runner/actions/workflows/python-app.yml)
[![regen-expected](https://github.com/dalozedidier-dot/Systemd-runner/actions/workflows/regen-expected.yml/badge.svg?branch=main&label=regen-expected)](https://github.com/dalozedidier-dot/Systemd-runner/actions/workflows/regen-expected.yml)

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/dalozedidier-dot/Systemd-runner)](LICENSE)

> Note : le message GitHub “Uh oh! There was an error while loading” est un artefact d’interface (côté GitHub).
> Il n’est pas un invariant du projet. Préférer les URLs *Raw* si nécessaire.

## Quick start

### 1) Installation
```bash
python -m pip install -r requirements.txt
```

### 2) Core runner (stdlib-only)
```bash
python 00_core/scripts/run_ddr.py --help
```

### 3) Multisector harness (profils YAML → expected)
Depuis la racine du repo :
```bash
python 01_tests_multisector/harness.py --repo-root . --profiles 01_tests_multisector/tests/profiles
```

Pour régénérer les expected snapshots (changement intentionnel de comportement) :
```bash
python 01_tests_multisector/harness.py --repo-root . --profiles 01_tests_multisector/tests/profiles --update-expected
```

## Contrats (tests)
- Profils : `01_tests_multisector/tests/profiles/*.yaml`
- Fixtures : `01_tests_multisector/tests/fixtures/`
- Expected + hashes : `01_tests_multisector/tests/expected/`
- Résumé agrégé : `01_tests_multisector/tests/results.json`

## Intégrité (SHA256)
Deux régimes existent :
- **Index de fichiers** (binaire) : `FILE_INDEX_SHA256.txt` (type `sha256sum -c`).
- **Snapshots expected** (sémantique) : `*.report.sha256.txt` correspond au `hash_sha256` interne calculé sur JSON canonique (hors champ `hash_sha256`).

## Documentation
- Exécution : `RUNNING.md`
- Glossaire + règles épistémologiques : `00_core/docs/`
- Spécification DDR : `00_core/docs/SPEC_DDR_v0.3.1-final.md`

## Non‑objectifs
- Aucune interprétation des résultats.
- Aucune intégration Linux systemd (unit files) fournie dans ce dépôt.

