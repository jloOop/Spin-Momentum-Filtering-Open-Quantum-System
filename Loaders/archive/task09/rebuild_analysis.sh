#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-python3}"
"$PY" "$ROOT/scripts/analyze_native.py" --directory "$ROOT"
"$PY" "$ROOT/scripts/plot_native.py"
"$PY" "$ROOT/scripts/build_report.py"
printf 'DERIVED_ANALYSIS_REBUILT=%s\n' "$ROOT"
