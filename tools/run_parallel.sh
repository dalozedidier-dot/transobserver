#!/usr/bin/env bash
set -euo pipefail

FIXTURE_DIR="${1:?Usage: run_parallel.sh shared_fixtures/<cycle_id> [unified_cycles_root]}"
OUT_ROOT="${2:-unified_cycles}"

CYCLE_ID="$(basename "$FIXTURE_DIR")"
CYCLE_DIR="$OUT_ROOT/$CYCLE_ID"

mkdir -p "$CYCLE_DIR/input"
rsync -a "$FIXTURE_DIR/" "$CYCLE_DIR/input/"

# Default: run in mock mode so the module is runnable out of the box.
# When you plug real engines, replace these calls or gate them with an env var.
MODULE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$CYCLE_DIR/phio" "$CYCLE_DIR/systemd" "$CYCLE_DIR/sost"

python3 "$MODULE_ROOT/engines/mock_phio.py" "$CYCLE_DIR/input/fixture.json" "$CYCLE_DIR/phio"
python3 "$MODULE_ROOT/engines/mock_systemd.py" "$CYCLE_DIR/input/fixture.json" "$CYCLE_DIR/systemd"
python3 "$MODULE_ROOT/engines/mock_sost.py" "$CYCLE_DIR/sost"

python3 "$MODULE_ROOT/tools/build_unified_manifest.py" "$CYCLE_DIR" > "$CYCLE_DIR/unified_manifest.json"
echo "OK: $CYCLE_DIR"
