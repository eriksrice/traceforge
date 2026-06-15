#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PYTHONPATH:-src}"
export PYTHONDONTWRITEBYTECODE=1

echo "== TraceForge demo =="
echo

echo "1. Running tests"
"$PYTHON_BIN" -m pytest
echo

echo "2. Generating baseline, incident, and patched traces"
"$PYTHON_BIN" -m traceforge run --case baseline
"$PYTHON_BIN" -m traceforge run --case incident
"$PYTHON_BIN" -m traceforge run --case patched
echo

echo "3. Comparing baseline vs incident"
"$PYTHON_BIN" -m traceforge replay \
  --baseline traces/baseline_good.jsonl \
  --candidate traces/incident_bad.jsonl \
  --output traces/replay_baseline_vs_incident.json
echo

echo "4. Running seeded regression gate"
"$PYTHON_BIN" -m traceforge gate
echo

echo "5. Summary"
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
from traceforge.replay import read_comparison_artifact
from traceforge.gate import GATE_RESULT_ARTIFACT
import json

incident = read_comparison_artifact(Path("traces/replay_baseline_vs_incident.json"))
patched = read_comparison_artifact(Path("traces/replay_baseline_vs_patched.json"))
with GATE_RESULT_ARTIFACT.open("r", encoding="utf-8") as handle:
    gate = json.load(handle)

first = next(item for item in incident.comparisons if item.first_divergence)
print(f"bad_first_divergence={first.field_path}")
print(f"bad_expected={first.baseline_value}")
print(f"bad_observed={first.candidate_value}")
print(f"patched_status={patched.replay_status}")
print(f"gate_status={gate['gate_status']}")
PY
echo

echo "Artifacts:"
echo "- traces/baseline_good.jsonl"
echo "- traces/incident_bad.jsonl"
echo "- traces/patched_good.jsonl"
echo "- traces/replay_baseline_vs_incident.json"
echo "- traces/replay_baseline_vs_patched.json"
echo "- traces/regression_gate_result.json"
echo "- reports/first_divergence_report.md"
echo "- reports/incident_timeline.md"
echo "- reports/regression_gate_report.md"
