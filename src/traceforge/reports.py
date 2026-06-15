"""Trace-derived markdown report generation."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from traceforge.diff import ProtectedFieldComparison, TraceComparisonArtifact
from traceforge.models import EventType, GateResult, TraceEvent

FIRST_DIVERGENCE_REPORT = Path("reports/first_divergence_report.md")
INCIDENT_TIMELINE_REPORT = Path("reports/incident_timeline.md")
REGRESSION_GATE_REPORT = Path("reports/regression_gate_report.md")


def write_first_divergence_report(
    comparison: TraceComparisonArtifact,
    output_path: Path = FIRST_DIVERGENCE_REPORT,
) -> Path:
    """Write a markdown report for the first protected-field divergence."""

    first = _first_divergence(comparison)
    lines = [
        "# First Divergence Report",
        "",
        "## Run Pair",
        "",
        f"- Baseline trace: `{comparison.baseline_trace_id}`",
        f"- Candidate trace: `{comparison.candidate_trace_id}`",
        f"- Replay status: `{comparison.replay_status}`",
        "",
        "## First Unacceptable Divergence",
        "",
    ]

    if first is None:
        lines.extend(["No protected-field divergence was detected.", ""])
    else:
        lines.extend(
            [
                f"- Field: `{first.field_path}`",
                f"- Expected: `{first.baseline_value}`",
                f"- Observed: `{first.candidate_value}`",
                f"- Label: `{first.divergence_label}`",
                f"- Severity: `{first.divergence_severity}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Downstream Effects",
            "",
        ]
    )
    downstream = [item for item in comparison.comparisons if item.downstream_of]
    if downstream:
        lines.extend(
            f"- `{item.field_path}` changed from `{item.baseline_value}` to `{item.candidate_value}`."
            for item in downstream
        )
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Reproduction Command",
            "",
            "```bash",
            "python -m traceforge replay --baseline traces/baseline_good.jsonl --candidate traces/incident_bad.jsonl",
            "```",
            "",
        ]
    )
    return _write_markdown(output_path, lines)


def write_incident_timeline_report(
    baseline_events: Iterable[TraceEvent],
    incident_events: Iterable[TraceEvent],
    comparison: TraceComparisonArtifact,
    output_path: Path = INCIDENT_TIMELINE_REPORT,
) -> Path:
    """Write a markdown incident timeline from traces and comparison facts."""

    baseline = list(baseline_events)
    incident = list(incident_events)
    first = _first_divergence(comparison)

    lines = [
        "# Incident Timeline Report",
        "",
        "## Incident Summary",
        "",
        "The seeded incident is a prompt-regression wrong-tool-selection failure in the checkout API support triage workflow.",
        "",
        "## Run Metadata",
        "",
        f"- Baseline run: `{comparison.baseline_run_id}`",
        f"- Incident run: `{comparison.candidate_run_id}`",
        f"- Baseline events: `{len(baseline)}`",
        f"- Incident events: `{len(incident)}`",
        "",
        "## Timeline",
        "",
    ]

    lines.extend(_timeline_lines("Baseline", baseline))
    lines.extend([""])
    lines.extend(_timeline_lines("Incident", incident))
    lines.extend(["", "## First Divergence", ""])

    if first is None:
        lines.append("No protected-field divergence was detected.")
    else:
        lines.extend(
            [
                f"- Field: `{first.field_path}`",
                f"- Expected: `{first.baseline_value}`",
                f"- Observed: `{first.candidate_value}`",
                f"- Root label: `{comparison.root_divergence_label}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Downstream Impact",
            "",
        ]
    )
    downstream = [item for item in comparison.comparisons if item.downstream_of]
    lines.extend(
        f"- `{item.field_path}` changed downstream of `{item.downstream_of}`."
        for item in downstream
    )
    lines.extend(
        [
            "",
            "## Patch Status",
            "",
            "Patch validation is recorded in `traces/replay_baseline_vs_patched.json` and summarized by the regression gate report.",
            "",
        ]
    )
    return _write_markdown(output_path, lines)


def write_regression_gate_report(
    gate_result: GateResult,
    incident_comparison: TraceComparisonArtifact,
    patched_comparison: TraceComparisonArtifact,
    output_path: Path = REGRESSION_GATE_REPORT,
) -> Path:
    """Write the CI-style regression gate report."""

    lines = [
        "# Regression Gate Report",
        "",
        "## Gate Result",
        "",
        f"- Gate: `{gate_result.gate_name}`",
        f"- Status: `{gate_result.gate_status}`",
        f"- Incident: `{gate_result.incident_id}`",
        f"- Review required: `{gate_result.review_required}`",
        "",
        "## Checks",
        "",
        f"- Bad run status: `{incident_comparison.replay_status}`",
        f"- Bad run first divergence: `{incident_comparison.first_divergence_field}`",
        f"- Patched run status: `{patched_comparison.replay_status}`",
        f"- Patched first divergence: `{patched_comparison.first_divergence_field}`",
        "",
        "## Checked Traces",
        "",
    ]
    lines.extend(f"- `{path}`" for path in gate_result.checked_traces)
    lines.extend(["", "## Generated Reports", ""])
    lines.extend(f"- `{path}`" for path in gate_result.checked_reports)
    lines.extend(["", "## Blocking Reasons", ""])
    if gate_result.blocking_reasons:
        lines.extend(f"- {reason}" for reason in gate_result.blocking_reasons)
    else:
        lines.append("- None.")
    lines.append("")
    return _write_markdown(output_path, lines)


def _first_divergence(
    comparison: TraceComparisonArtifact,
) -> ProtectedFieldComparison | None:
    for item in comparison.comparisons:
        if item.first_divergence:
            return item
    return None


def _timeline_lines(label: str, events: List[TraceEvent]) -> List[str]:
    lines = [f"### {label}"]
    for event in events:
        if event.event_type in {
            EventType.MODEL_CALL,
            EventType.TOOL_CALL,
            EventType.STATE_TRANSITION,
        }:
            detail = _event_detail(event)
            lines.append(
                f"- Step {event.step_index} `{event.step_name}` `{event.event_type}`: {detail}"
            )
    return lines


def _event_detail(event: TraceEvent) -> str:
    if event.model_call:
        return f"fixture `{event.model_call.model_fixture_id}`"
    if event.tool_call:
        return f"tool `{event.tool_call.tool_name}` fixture `{event.tool_call.tool_fixture_id}`"
    if event.state_transition:
        return f"transition `{event.state_transition.transition_label}`"
    return "event recorded"


def _write_markdown(path: Path, lines: List[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
