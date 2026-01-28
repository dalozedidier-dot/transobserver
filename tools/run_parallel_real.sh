#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash tools/run_parallel_real.sh shared_fixtures/<cycle_id> unified_cycles
#
# Integrated engines:
#   engines/phio
#   engines/systemd-runner
#   engines/sost

FIXTURE_DIR="${1:?Usage: run_parallel_real.sh shared_fixtures/<cycle_id> [unified_cycles_root]}"
OUT_ROOT="${2:-unified_cycles}"

CYCLE_ID="$(basename "$FIXTURE_DIR")"
CYCLE_DIR="$OUT_ROOT/$CYCLE_ID"

MODULE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$CYCLE_DIR/input"
rsync -a "$FIXTURE_DIR/" "$CYCLE_DIR/input/"

mkdir -p "$CYCLE_DIR/phio" "$CYCLE_DIR/systemd" "$CYCLE_DIR/sost"

# PhiO (contract_probe + manifest)
python3 "$MODULE_ROOT/tools/phio_run.py" "$CYCLE_DIR/input/fixture.json" "$CYCLE_DIR/phio" || true

# SystemD (DD-R + E when runnable; otherwise emits a skipped extraction_report + manifest)
python3 "$MODULE_ROOT/tools/systemd_run.py" "$CYCLE_DIR/input/fixture.json" "$CYCLE_DIR/systemd" || true

# SOST
python3 "$MODULE_ROOT/tools/sost_run.py" "$CYCLE_DIR/input/fixture.json" "$CYCLE_DIR/sost" || true

# Ensure systemd manifest exists (belt and suspenders)
if [ -d "$CYCLE_DIR/systemd" ] && [ ! -f "$CYCLE_DIR/systemd/run_manifest.json" ]; then
  python3 "$MODULE_ROOT/tools/systemd_make_manifest.py" --input "$CYCLE_DIR/input/fixture.json" --out "$CYCLE_DIR/systemd" || true
fi

python3 "$MODULE_ROOT/tools/build_unified_manifest.py" "$CYCLE_DIR" > "$CYCLE_DIR/unified_manifest.json"
echo "OK: $CYCLE_DIR"
