"""CI-style regression gate for the seeded TraceForge incident."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from traceforge.models import (
    DivergenceLabel,
    GateResult,
    GateStatus,
    ReplayMode,
    ReplayStatus,
)
from traceforge.replay import compare_trace_files
from traceforge.reports import (
    FIRST_DIVERGENCE_REPORT,
    INCIDENT_TIMELINE_REPORT,
    REGRESSION_GATE_REPORT,
    write_first_divergence_report,
    write_incident_timeline_report,
    write_regression_gate_report,
)
from traceforge.tracing import read_trace
from traceforge.workflow import run_workflow

GATE_NAME = "traceforge-seeded-regression"
INCIDENT_ID = "checkout_timeout_wrong_tool"
GATE_RESULT_ARTIFACT = Path("traces/regression_gate_result.json")
INCIDENT_COMPARISON_ARTIFACT = Path("traces/replay_baseline_vs_incident.json")
PATCHED_COMPARISON_ARTIFACT = Path("traces/replay_baseline_vs_patched.json")


def run_gate(
    *,
    trace_dir: Path = Path("traces"),
    report_dir: Path = Path("reports"),
    overwrite: bool = True,
) -> GateResult:
    """Run the seeded regression gate and write all Phase 6 artifacts."""

    baseline = run_workflow("baseline", output_dir=trace_dir, overwrite=overwrite)
    incident = run_workflow("incident", output_dir=trace_dir, overwrite=overwrite)
    patched = run_workflow("patched", output_dir=trace_dir, overwrite=overwrite)

    incident_comparison_path = trace_dir / INCIDENT_COMPARISON_ARTIFACT.name
    patched_comparison_path = trace_dir / PATCHED_COMPARISON_ARTIFACT.name

    incident_comparison = compare_trace_files(
        baseline.trace_path,
        incident.trace_path,
        output_path=incident_comparison_path,
        replay_mode=ReplayMode.INCIDENT,
        overwrite=overwrite,
    )
    patched_comparison = compare_trace_files(
        baseline.trace_path,
        patched.trace_path,
        output_path=patched_comparison_path,
        replay_mode=ReplayMode.PATCHED,
        overwrite=overwrite,
    )

    first_report = report_dir / FIRST_DIVERGENCE_REPORT.name
    timeline_report = report_dir / INCIDENT_TIMELINE_REPORT.name
    gate_report = report_dir / REGRESSION_GATE_REPORT.name

    write_first_divergence_report(incident_comparison, first_report)
    write_incident_timeline_report(
        read_trace(baseline.trace_path),
        read_trace(incident.trace_path),
        incident_comparison,
        timeline_report,
    )

    blocking_reasons = _blocking_reasons(incident_comparison, patched_comparison)
    gate_result = GateResult(
        gate_name=GATE_NAME,
        gate_status=GateStatus.FAIL if blocking_reasons else GateStatus.PASS,
        incident_id=INCIDENT_ID,
        checked_traces=(
            str(baseline.trace_path),
            str(incident.trace_path),
            str(patched.trace_path),
            str(incident_comparison_path),
            str(patched_comparison_path),
        ),
        checked_reports=(
            str(first_report),
            str(timeline_report),
            str(gate_report),
        ),
        blocking_reasons=tuple(blocking_reasons),
        review_required=bool(blocking_reasons),
        notes="Bad run fails for expected first divergence; patched run must match baseline protected fields.",
    )
    write_regression_gate_report(
        gate_result,
        incident_comparison,
        patched_comparison,
        gate_report,
    )
    _write_gate_result(gate_result, trace_dir / GATE_RESULT_ARTIFACT.name)
    return gate_result


def _blocking_reasons(
    incident_comparison,
    patched_comparison,
) -> List[str]:
    reasons: List[str] = []
    if incident_comparison.replay_status != ReplayStatus.DIVERGED_UNACCEPTABLE:
        reasons.append("bad incident run did not diverge as expected")
    if incident_comparison.first_divergence_field != "step_1.output.requested_tool":
        reasons.append("bad incident first divergence was not Step 1 requested_tool")
    if incident_comparison.root_divergence_label != DivergenceLabel.TOOL_SELECTION_CHANGED:
        reasons.append("bad incident root divergence was not tool_selection_changed")
    if patched_comparison.replay_status != ReplayStatus.MATCHED:
        reasons.append("patched run diverged from baseline on protected fields")
    if patched_comparison.first_divergence_field is not None:
        reasons.append("patched run still has a first divergence")
    return reasons


def _write_gate_result(gate_result: GateResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(gate_result.model_dump(mode="json"), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path
