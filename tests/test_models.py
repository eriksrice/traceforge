from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from traceforge.models import (
    DeterminismClass,
    DivergenceLabel,
    DivergenceSeverity,
    EventStatus,
    EventType,
    GateResult,
    GateStatus,
    ModelCallPayload,
    ModelOutputMode,
    ReplayComparison,
    ReplayMode,
    ReplayStatus,
    StepName,
    ToolCallPayload,
    ToolReplayMode,
    ToolStatus,
    TraceEvent,
    V1_PROTECTED_FIELDS,
)


def _timestamp() -> datetime:
    return datetime(2026, 6, 12, 15, 42, tzinfo=timezone.utc)


def test_trace_event_requires_matching_payload() -> None:
    with pytest.raises(ValidationError):
        TraceEvent(
            event_id="event_1",
            trace_id="trace_1",
            run_id="run_1",
            step_index=1,
            step_name=StepName.INTAKE_ROUTE,
            event_type=EventType.MODEL_CALL,
            timestamp_start=_timestamp(),
            status=EventStatus.SUCCESS,
        )


def test_model_call_cached_outputs_require_fixture_metadata() -> None:
    with pytest.raises(ValidationError):
        ModelCallPayload(
            model_provider="synthetic",
            model_name="fixture",
            model_version="v1",
            prompt_id="triage_route_prompt",
            prompt_version="triage_route_prompt:v1",
            prompt_hash="sha256:prompt",
            input_hash="sha256:input",
            output_hash="sha256:output",
            model_output_mode=ModelOutputMode.CACHED,
        )


def test_tool_call_mocked_replay_requires_fixture_metadata() -> None:
    with pytest.raises(ValidationError):
        ToolCallPayload(
            tool_name="service_metrics_lookup",
            tool_version="v1",
            tool_call_id="tool_call_1",
            tool_input={"service": "checkout-api"},
            tool_input_hash="sha256:input",
            tool_output={"status": "ok"},
            tool_status=ToolStatus.SUCCESS,
            tool_replay_mode=ToolReplayMode.MOCKED,
        )


def test_replay_comparison_accepts_first_requested_tool_divergence() -> None:
    comparison = ReplayComparison(
        baseline_event_id="baseline_event_1",
        replay_event_id="incident_event_1",
        replay_mode=ReplayMode.INCIDENT,
        replay_status=ReplayStatus.DIVERGED_UNACCEPTABLE,
        determinism_class=DeterminismClass.DETERMINISTIC,
        divergence_label=DivergenceLabel.TOOL_SELECTION_CHANGED,
        divergence_severity=DivergenceSeverity.BLOCKING,
        first_divergence=True,
        root_divergence_event_id="incident_event_1",
    )

    assert comparison.divergence_label == DivergenceLabel.TOOL_SELECTION_CHANGED


def test_failed_gate_requires_blocking_reason() -> None:
    with pytest.raises(ValidationError):
        GateResult(
            gate_name="traceforge-seeded-regression",
            gate_status=GateStatus.FAIL,
            incident_id="checkout_timeout_wrong_tool",
        )


def test_protected_fields_include_requested_tool() -> None:
    assert "step_1.output.requested_tool" in V1_PROTECTED_FIELDS
