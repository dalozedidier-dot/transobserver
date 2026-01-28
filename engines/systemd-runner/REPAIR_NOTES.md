# REPAIR_NOTES — SystemD v0.3.1 — repair overlay

## Fix applied: multisector harness path resolution

Symptom:
- Running the harness from repository root with profiles using `tests/...` relative paths fails
  because fixtures/expected live under `01_tests_multisector/tests/...` in the repository layout.

Change:
- `01_tests_multisector/harness.py` now resolves any `tests/...` path as:
  `01_tests_multisector/tests/...` (when present), while keeping backward compatibility.

Effects:
- The command documented in RUNNING.md works from repository root:
  `python 01_tests_multisector/harness.py --repo-root .`

## Additions
- `LICENSE` (MIT).
- `00_core/scripts/verify_file_index.py` and `00_core/scripts/make_file_index.py` (cross-platform integrity tooling).
