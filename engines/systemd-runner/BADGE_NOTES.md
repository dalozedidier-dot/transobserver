# BADGE_NOTES — v0.3.1.3

Constat : deux workflows distincts (`ci.yml` et `python-app.yml`) portent le même `name: systemd-ci`.
Effet : duplication potentielle dans l’onglet Actions.

Ce correctif ajoute des badges *testables* (URL = fichier workflow, pas `name:`) :
- `actions/workflows/ci.yml`
- `actions/workflows/python-app.yml`
- `actions/workflows/regen-expected.yml`

Option de nettoyage :
- conserver un seul workflow de CI (ci.yml **ou** python-app.yml) pour supprimer le doublon `systemd-ci`.
