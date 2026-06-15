"""First-divergence comparison for protected TraceForge fields."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from pydantic import Field

from traceforge.models import (
    DeterminismClass,
    DivergenceLabel,
    DivergenceSeverity,
    EventType,
    ReplayMode,
    ReplayStatus,
    TraceEvent,
    TraceForgeModel,
    V1_PROTECTED_FIELDS,
)


class TraceDiffError(ValueError):
    """Raised when traces cannot be compared."""


class ProtectedFieldComparison(TraceForgeModel):
    """Comparison result for one protected field."""

    field_path: str = Field(min_length=1)
    baseline_value: Any = None
    candidate_value: Any = None
    matched: bool
    divergence_label: DivergenceLabel
    divergence_severity: DivergenceSeverity
    first_divergence: bool = False
    downstream_of: Optional[str] = None
    note: str = ""


class TraceComparisonArtifact(TraceForgeModel):
    """Run-level replay comparison artifact."""

    artifact_type: str = "traceforge.replay_comparison.v1"
    baseline_trace_id: str = Field(min_length=1)
    candidate_trace_id: str = Field(min_length=1)
    baseline_run_id: str = Field(min_length=1)
    candidate_run_id: str = Field(min_length=1)
    replay_mode: ReplayMode
    replay_status: ReplayStatus
    determinism_class: DeterminismClass
    protected_field_order: tuple[str, ...]
    comparisons: tuple[ProtectedFieldComparison, ...]
    first_divergence_field: Optional[str] = None
    first_divergence_step_index: Optional[int] = None
    root_divergence_label: DivergenceLabel = DivergenceLabel.NONE
    root_divergence_event_id: Optional[str] = None


class TraceProtectedSnapshot(TraceForgeModel):
    """Extracted protected values from a typed trace."""

    trace_id: str
    run_id: str
    protected_values: Dict[str, Any]
    source_event_ids: Dict[str, str]


def compare_trace_events(
    baseline_events: Iterable[TraceEvent],
    candidate_events: Iterable[TraceEvent],
    *,
    replay_mode: ReplayMode = ReplayMode.INCIDENT,
) -> TraceComparisonArtifact:
    """Compare two traces on v1 protected fields."""

    baseline = extract_protected_snapshot(baseline_events)
    candidate = extract_protected_snapshot(candidate_events)

    first_divergence: Optional[ProtectedFieldComparison] = None
    comparisons: List[ProtectedFieldComparison] = []

    for field_path in V1_PROTECTED_FIELDS:
        baseline_value = baseline.protected_values.get(field_path)
        candidate_value = candidate.protected_values.get(field_path)
        matched = baseline_value == candidate_value

        if matched:
            comparison = ProtectedFieldComparison(
                field_path=field_path,
                baseline_value=baseline_value,
                candidate_value=candidate_value,
                matched=True,
                divergence_label=DivergenceLabel.NONE,
                divergence_severity=DivergenceSeverity.NONE,
            )
        else:
            is_first = first_divergence is None
            label = _label_for_field(field_path)
            comparison = ProtectedFieldComparison(
                field_path=field_path,
                baseline_value=baseline_value,
                candidate_value=candidate_value,
                matched=False,
                divergence_label=label,
                divergence_severity=DivergenceSeverity.BLOCKING
                if is_first
                else DivergenceSeverity.WARNING,
                first_divergence=is_first,
                downstream_of=None
                if is_first
                else first_divergence.field_path
                if first_divergence
                else None,
                note="root protected-field divergence"
                if is_first
                else "downstream effect of first divergence",
            )
            if is_first:
                first_divergence = comparison

        comparisons.append(comparison)

    first_field = first_divergence.field_path if first_divergence else None
    root_event_id = (
        candidate.source_event_ids.get(first_field) if first_field is not None else None
    )
    replay_status = (
        ReplayStatus.DIVERGED_UNACCEPTABLE
        if first_divergence
        else ReplayStatus.MATCHED
    )

    return TraceComparisonArtifact(
        baseline_trace_id=baseline.trace_id,
        candidate_trace_id=candidate.trace_id,
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        replay_mode=replay_mode,
        replay_status=replay_status,
        determinism_class=DeterminismClass.DETERMINISTIC,
        protected_field_order=V1_PROTECTED_FIELDS,
        comparisons=tuple(comparisons),
        first_divergence_field=first_field,
        first_divergence_step_index=_step_index_for_field(first_field),
        root_divergence_label=first_divergence.divergence_label
        if first_divergence
        else DivergenceLabel.NONE,
        root_divergence_event_id=root_event_id,
    )


def extract_protected_snapshot(
    events: Iterable[TraceEvent],
) -> TraceProtectedSnapshot:
    """Extract protected field values from one trace."""

    event_list = list(events)
    if not event_list:
        raise TraceDiffError("cannot compare an empty trace")

    trace_id = event_list[0].trace_id
    run_id = event_list[0].run_id
    if any(event.trace_id != trace_id for event in event_list):
        raise TraceDiffError("trace contains multiple trace_id values")
    if any(event.run_id != run_id for event in event_list):
        raise TraceDiffError("trace contains multiple run_id values")

    state_events = {
        event.step_index: event
        for event in event_list
        if event.event_type == EventType.STATE_TRANSITION and event.state_transition
    }
    tool_events = {
        event.step_index: event
        for event in event_list
        if event.event_type == EventType.TOOL_CALL and event.tool_call
    }

    values: Dict[str, Any] = {"trace.schema_valid": True}
    source_event_ids: Dict[str, str] = {}

    step_1_state = _required_state_event(state_events, 1)
    step_2_state = _required_state_event(state_events, 2)
    step_3_state = _required_state_event(state_events, 3)
    step_2_tool = _required_tool_event(tool_events, 2)

    _put(values, source_event_ids, "step_1.output.requested_tool", step_1_state, "requested_tool")
    _put(values, source_event_ids, "step_1.output.diagnostic_route", step_1_state, "diagnostic_route")
    values["step_1.state.transition_label"] = step_1_state.state_transition.transition_label
    source_event_ids["step_1.state.transition_label"] = step_1_state.event_id

    values["step_2.tool_name"] = step_2_tool.tool_call.tool_name
    source_event_ids["step_2.tool_name"] = step_2_tool.event_id
    _put(values, source_event_ids, "step_2.output.evidence_family", step_2_state, "evidence_family")
    values["step_2.state.transition_label"] = step_2_state.state_transition.transition_label
    source_event_ids["step_2.state.transition_label"] = step_2_state.event_id

    _put(values, source_event_ids, "step_3.output.incident_type", step_3_state, "incident_type")
    _put(values, source_event_ids, "step_3.output.severity", step_3_state, "severity")
    _put(
        values,
        source_event_ids,
        "step_3.output.engineering_next_action",
        step_3_state,
        "engineering_next_action",
    )
    _put(
        values,
        source_event_ids,
        "step_3.output.escalation_required",
        step_3_state,
        "escalation_required",
    )
    values["step_3.state.transition_label"] = step_3_state.state_transition.transition_label
    source_event_ids["step_3.state.transition_label"] = step_3_state.event_id
    source_event_ids["trace.schema_valid"] = event_list[0].event_id

    return TraceProtectedSnapshot(
        trace_id=trace_id,
        run_id=run_id,
        protected_values=values,
        source_event_ids=source_event_ids,
    )


def _put(
    values: Dict[str, Any],
    source_event_ids: Dict[str, str],
    field_path: str,
    event: TraceEvent,
    patch_key: str,
) -> None:
    values[field_path] = event.state_transition.state_patch.get(patch_key)
    source_event_ids[field_path] = event.event_id


def _required_state_event(events: Dict[int, TraceEvent], step_index: int) -> TraceEvent:
    if step_index not in events:
        raise TraceDiffError(f"missing state transition event for step {step_index}")
    return events[step_index]


def _required_tool_event(events: Dict[int, TraceEvent], step_index: int) -> TraceEvent:
    if step_index not in events:
        raise TraceDiffError(f"missing tool call event for step {step_index}")
    return events[step_index]


def _label_for_field(field_path: str) -> DivergenceLabel:
    if field_path in {
        "step_1.output.requested_tool",
        "step_2.tool_name",
    }:
        return DivergenceLabel.TOOL_SELECTION_CHANGED
    if field_path == "step_2.output.evidence_family":
        return DivergenceLabel.TOOL_RESPONSE_CHANGED
    if field_path.startswith("step_1.output."):
        return DivergenceLabel.PROMPT_OUTPUT_CHANGED
    if field_path.startswith("step_3.output."):
        return DivergenceLabel.PROMPT_OUTPUT_CHANGED
    if ".state.transition_label" in field_path:
        return DivergenceLabel.STATE_TRANSITION_CHANGED
    if field_path == "trace.schema_valid":
        return DivergenceLabel.SCHEMA_VIOLATION
    return DivergenceLabel.STATE_TRANSITION_CHANGED


def _step_index_for_field(field_path: Optional[str]) -> Optional[int]:
    if field_path is None:
        return None
    if field_path.startswith("step_1."):
        return 1
    if field_path.startswith("step_2."):
        return 2
    if field_path.startswith("step_3."):
        return 3
    return None
