# CI_FIX_NOTES — v0.3.1.1

Symptom (CI):
- `verify_file_index.py` fails on `01_tests_multisector/tests/results.json` because `FILE_INDEX_SHA256.txt`
  is out-of-sync with the repository snapshot.

Fix applied:
1) Replace `FILE_INDEX_SHA256.txt` with a regenerated version for the current tree.
   - `01_tests_multisector/tests/results.json` hash in this snapshot: 9e65d1ddbc2636eb8cc15dd9007703d03c9ea1af75e62bdbbce8afe5c93b39fe
2) Update `.github/workflows/ci.yml` so that:
   - integrity verification runs before any generator step,
   - the harness writes results to `/tmp/systemd_results.json` (does not mutate tracked files).

Deterministic rule:
- If you commit changes that modify any tracked file, regenerate `FILE_INDEX_SHA256.txt` and commit it.
