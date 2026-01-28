# CI_REPAIR_NOTES — v0.3.1

This overlay provides a replacement `.github/workflows/ci.yml` aligned with the repository layout.

Invariants enforced in CI:
- requirements.txt installed (PyYAML for harness)
- core self-tests: `python 00_core/scripts/run_ddr.py --run-tests`
- file index verification: `python 00_core/scripts/verify_file_index.py --root .`
- multisector harness from repo root: `python 01_tests_multisector/harness.py --repo-root .`

If your repository already contains `ci.yml`, replace it with this one.
