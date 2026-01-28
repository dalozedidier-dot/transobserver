# RUNNING — SystemD v0.3.1 (Core + Multisector Tests + Sectors)

Document version: RUNNING_v0.3.1.0

## 0) Scope

This repository / OSF project is organized around a single baseline (v0.3.1) and a structured split into sector components.

- **00_core**: DD-R runner + specifications + templates (stdlib-only).
- **01_tests_multisector**: cross-sector test harness (requires PyYAML).
- **SXX_<sector>**: sector specializations (inputs/params/adapters/outputs/notes).
- **99_releases**: frozen exports (zips, checksums, indexes).

This document describes how to execute the **core runner** and the **multisector tests**.

## 1) Requirements

- Python **3.9+** recommended (3.8+ should also work for stdlib-only parts).
- For the test harness: install dependencies from `requirements.txt`.

### Install (for tests)
```bash
python -m pip install -r requirements.txt
```

## 2) Expected Paths

Two equivalent layouts are supported:

### A) OSF / repository layout (recommended)
```
00_core/
01_tests_multisector/
SXX_<sector>/
99_releases/
requirements.txt
RUNNING.md
```

### B) Release zip layout (core-only bundle)
If you downloaded an export zip, you may have a single folder such as:
```
SystemD_online_final_v0.3.1-final/
  scripts/
  specs/
  templates/
  examples/
  docs/
```

## 3) Run the Core DD-R Runner (00_core)

### Inputs
The runner expects an observation matrix file `TEST_MATRIX.md`.

- Use your own `TEST_MATRIX.md`, or
- Start from the template: `00_core/templates/TEST_MATRIX.template.md`, or
- Use the example: `00_core/examples/TEST_MATRIX.example.md`.

### Command (OSF / repository layout)
From the repository root:
```bash
python 00_core/scripts/run_ddr.py --test-matrix 00_core/examples/TEST_MATRIX.example.md --out 00_core/outputs
```

To run on your own matrix:
```bash
python 00_core/scripts/run_ddr.py --test-matrix PATH/TO/TEST_MATRIX.md --out outputs
```

### Outputs
The runner writes deterministic JSON reports:
- `ddr_report.json` (invariants, divergence, DDR classification, statuses)
- `extraction_report.json` (detected sections, item counts, unassigned lines)
- `e_report.json` (optional, if E is enabled by the runner/spec)

Output directory is controlled by `--out`.

### Optional: self-tests (stdlib unittest)
```bash
python 00_core/scripts/run_ddr.py --run-tests
```

## 4) Run the Multisector Test Harness (01_tests_multisector)

### Purpose
The harness runs YAML “profiles-as-contract” against fixtures and compares results to expected SHA256 snapshots.

### Command
From the repository root:
```bash
python 01_tests_multisector/harness.py --repo-root . --profiles 01_tests_multisector/tests/profiles
```

### Expected artifacts
- Aggregated results (when enabled by the harness): `01_tests_multisector/tests/results.json`
- Expected outputs and hashes live in: `01_tests_multisector/tests/expected/`

### Updating expected snapshots (only when intentionally changing behavior)
```bash
python 01_tests_multisector/harness.py --repo-root . --profiles 01_tests_multisector/tests/profiles --update-expected
```

## 5) Integrity / Checksums (optional but recommended)

If a release bundle includes `FILE_INDEX_SHA256.txt`, you can verify file integrity after download/unzip.

Example (Linux/macOS):
```bash
sha256sum -c FILE_INDEX_SHA256.txt
```

On Windows (PowerShell), use `Get-FileHash` and compare manually or via a script.

## 6) Known Friction Points (non-blocking)

- Some documentation strings may still reference `v0.3.0` (legacy naming), while the runner is `v0.3.1-final`.
  This does not prevent execution; prefer the commands in this document.

## 7) What this does NOT cover

- Sector-specific adapter implementations beyond the minimal layout.
- Any interpretation of results. This repository is descriptive and contract-driven.
