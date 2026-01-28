# SXX_TEMPLATE_sector

Template minimal opérationnel pour sectorisation (STRUCT_N).
Objectif : fournir un exemple reproductible (profiles + fixtures) sans dépendre du multisector.

## Exécution (depuis la racine du repo)
pip install -r requirements.txt

# Génération initiale des expected
python 01_tests_multisector/harness.py --repo-root . --profiles SXX_TEMPLATE_sector/tests/profiles --update-expected

# Vérification (sans update)
python 01_tests_multisector/harness.py --repo-root . --profiles SXX_TEMPLATE_sector/tests/profiles
