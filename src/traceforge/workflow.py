"""Deterministic 3-step incident triage workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from traceforge.fixtures import CaseFixtures, fixture_hash, load_case_fixtures
from traceforge.hashing import stable_hash
from traceforge.models import (
    EventStatus,
    EventType,
    ModelCallPayload,
    ModelOutputMode,
    StateTransitionPayload,
    StepName,
    ToolCallPayload,
    ToolReplayMode,
    ToolStatus,
    TraceEvent,
    V1_PROTECTED_FIELDS,
)
from traceforge.tracing import TraceWriter

CASE_TRACE_FILES = {
    "baseline": "baseline_good.jsonl",
    "incident": "incident_bad.jsonl",
    "patched": "patched_good.jsonl",
}

CASE_RUN_IDS = {
    "baseline": "baseline_good",
    "incident": "incident_bad",
    "patched": "patched_good",
}

BASE_TIMESTAMP = datetime(2026, 6, 12, 15, 42, tzinfo=timezone.utc)


@dataclass(frozen=True)
class WorkflowRunResult:
    """Result of one deterministic workflow run."""

    case_name: str
    trace_id: str
    run_id: str
    events: Tuple[TraceEvent, ...]
    final_state: Dict[str, Any]
    trace_path: Optional[Path] = None


def run_workflow(
    case_name: str,
    *,
    output_dir: Path = Path("traces"),
    write_trace: bool = True,
    overwrite: bool = True,
) -> WorkflowRunResult:
    """Run a deterministic fixture-backed case and optionally write its trace."""

    fixtures = load_case_fixtures(case_name)
    run_id = CASE_RUN_IDS[case_name]
    trace_id = f"trace_checkout_timeout_{run_id}"

    events, final_state = build_trace_events(fixtures, trace_id=trace_id, run_id=run_id)
    trace_path = None
    if write_trace:
        trace_path = output_dir / CASE_TRACE_FILES[case_name]
        TraceWriter(trace_path, overwrite=overwrite).write_events(events)

    return WorkflowRunResult(
        case_name=case_name,
        trace_id=trace_id,
        run_id=run_id,
        events=tuple(events),
        final_state=final_state,
        trace_path=trace_path,
    )


def build_trace_events(
    fixtures: CaseFixtures,
    *,
    trace_id: str,
    run_id: str,
) -> Tuple[List[TraceEvent], Dict[str, Any]]:
    """Build typed trace events for the 3-step fixture-backed workflow."""

    context = _EventContext(trace_id=trace_id, run_id=run_id)
    events: List[TraceEvent] = []
    state: Dict[str, Any] = {
        "case_id": fixtures.incident.case_id,
        "customer_id": fixtures.incident.customer["customer_id"],
        "status": "initialized",
    }

    events.extend(_run_intake_route(context, fixtures, state))
    events.extend(_run_collect_evidence(context, fixtures, state))
    events.extend(_run_classify_incident(context, fixtures, state))

    return events, state


@dataclass
class _EventContext:
    trace_id: str
    run_id: str
    ordinal: int = 0

    def next_event_id(self, step_index: int, event_type: EventType) -> str:
        self.ordinal += 1
        return stable_hash(
            {
                "run_id": self.run_id,
                "step_index": step_index,
                "event_type": event_type.value,
                "ordinal": self.ordinal,
            },
            prefix="evt",
        )

    def timestamp(self) -> datetime:
        return BASE_TIMESTAMP + timedelta(milliseconds=self.ordinal * 10)


def _run_intake_route(
    context: _EventContext,
    fixtures: CaseFixtures,
    state: Dict[str, Any],
) -> List[TraceEvent]:
    step_index = 1
    step_name = StepName.INTAKE_ROUTE
    events = [_step_event(context, step_index, step_name, EventType.STEP_START)]

    route = fixtures.route
    model_payload = ModelCallPayload(
        model_provider=route.model_provider,
        model_name=route.model_name,
        model_version=route.model_version,
        temperature=None,
        seed=0,
        prompt_id=route.prompt_id,
        prompt_version=route.prompt_version,
        prompt_hash=stable_hash(
            {"prompt_id": route.prompt_id, "prompt_version": route.prompt_version}
        ),
        system_prompt_hash=None,
        input_hash=fixture_hash(fixtures.incident),
        output_hash=stable_hash(route.output),
        token_input_count=None,
        token_output_count=None,
        estimated_cost_usd=None,
        model_output_mode=ModelOutputMode.CACHED,
        model_fixture_id=route.fixture_id,
        model_fixture_version=route.fixture_version,
    )
    events.append(
        _step_event(
            context,
            step_index,
            step_name,
            EventType.MODEL_CALL,
            model_call=model_payload,
        )
    )

    before = dict(state)
    state.update(
        {
            "status": "route_selected",
            "route": route.output,
            "requested_tool": route.output["requested_tool"],
            "diagnostic_route": route.output["diagnostic_route"],
        }
    )
    events.append(
        _state_event(
            context,
            step_index,
            step_name,
            before,
            state,
            transition_label="route_selected",
            state_patch={
                "route": route.output,
                "requested_tool": route.output["requested_tool"],
                "diagnostic_route": route.output["diagnostic_route"],
            },
            changed_fields=(
                "route",
                "requested_tool",
                "diagnostic_route",
                "status",
            ),
        )
    )
    events.append(_step_event(context, step_index, step_name, EventType.STEP_END))
    return events


def _run_collect_evidence(
    context: _EventContext,
    fixtures: CaseFixtures,
    state: Dict[str, Any],
) -> List[TraceEvent]:
    step_index = 2
    step_name = StepName.COLLECT_EVIDENCE
    events = [_step_event(context, step_index, step_name, EventType.STEP_START)]

    tool = fixtures.tool
    tool_payload = ToolCallPayload(
        tool_name=tool.tool_name,
        tool_version=tool.tool_version,
        tool_call_id=stable_hash(
            {"run_id": context.run_id, "tool_name": tool.tool_name}, prefix="tool_call"
        ),
        tool_input=tool.input,
        tool_input_hash=stable_hash(tool.input),
        tool_output=tool.output,
        tool_output_hash=stable_hash(tool.output),
        tool_latency_ms=tool.latency_ms,
        tool_status=ToolStatus.SUCCESS,
        tool_error_type=None,
        tool_fixture_id=tool.fixture_id,
        tool_fixture_version=tool.fixture_version,
        tool_replay_mode=ToolReplayMode.MOCKED,
    )
    events.append(
        _step_event(
            context,
            step_index,
            step_name,
            EventType.TOOL_CALL,
            tool_call=tool_payload,
        )
    )

    before = dict(state)
    state.update(
        {
            "status": "evidence_collected",
            "tool_name": tool.tool_name,
            "evidence": tool.output,
            "evidence_family": tool.output["evidence_family"],
        }
    )
    events.append(
        _state_event(
            context,
            step_index,
            step_name,
            before,
            state,
            transition_label="evidence_collected",
            state_patch={
                "tool_name": tool.tool_name,
                "evidence": tool.output,
                "evidence_family": tool.output["evidence_family"],
            },
            changed_fields=("tool_name", "evidence", "evidence_family", "status"),
        )
    )
    events.append(_step_event(context, step_index, step_name, EventType.STEP_END))
    return events


def _run_classify_incident(
    context: _EventContext,
    fixtures: CaseFixtures,
    state: Dict[str, Any],
) -> List[TraceEvent]:
    step_index = 3
    step_name = StepName.CLASSIFY_INCIDENT
    events = [_step_event(context, step_index, step_name, EventType.STEP_START)]

    classification = fixtures.classification
    model_payload = ModelCallPayload(
        model_provider=classification.model_provider,
        model_name=classification.model_name,
        model_version=classification.model_version,
        temperature=None,
        seed=0,
        prompt_id=classification.prompt_id,
        prompt_version=classification.prompt_version,
        prompt_hash=stable_hash(
            {
                "prompt_id": classification.prompt_id,
                "prompt_version": classification.prompt_version,
            }
        ),
        system_prompt_hash=None,
        input_hash=stable_hash(
            {
                "route": state["route"],
                "evidence": state["evidence"],
            }
        ),
        output_hash=stable_hash(classification.output),
        token_input_count=None,
        token_output_count=None,
        estimated_cost_usd=None,
        model_output_mode=ModelOutputMode.CACHED,
        model_fixture_id=classification.fixture_id,
        model_fixture_version=classification.fixture_version,
    )
    events.append(
        _step_event(
            context,
            step_index,
            step_name,
            EventType.MODEL_CALL,
            model_call=model_payload,
        )
    )

    before = dict(state)
    state.update(
        {
            "status": "incident_classified",
            "classification": classification.output,
            "incident_type": classification.output["incident_type"],
            "severity": classification.output["severity"],
            "engineering_next_action": classification.output[
                "engineering_next_action"
            ],
            "escalation_required": classification.output["escalation_required"],
        }
    )
    events.append(
        _state_event(
            context,
            step_index,
            step_name,
            before,
            state,
            transition_label="incident_classified",
            state_patch={
                "classification": classification.output,
                "incident_type": classification.output["incident_type"],
                "severity": classification.output["severity"],
                "engineering_next_action": classification.output[
                    "engineering_next_action"
                ],
                "escalation_required": classification.output["escalation_required"],
            },
            changed_fields=(
                "classification",
                "incident_type",
                "severity",
                "engineering_next_action",
                "escalation_required",
                "status",
            ),
        )
    )
    events.append(_step_event(context, step_index, step_name, EventType.STEP_END))
    return events


def _step_event(
    context: _EventContext,
    step_index: int,
    step_name: StepName,
    event_type: EventType,
    *,
    model_call: Optional[ModelCallPayload] = None,
    tool_call: Optional[ToolCallPayload] = None,
) -> TraceEvent:
    timestamp_start = context.timestamp()
    return TraceEvent(
        event_id=context.next_event_id(step_index, event_type),
        trace_id=context.trace_id,
        run_id=context.run_id,
        step_index=step_index,
        step_name=step_name,
        event_type=event_type,
        timestamp_start=timestamp_start,
        timestamp_end=timestamp_start,
        latency_ms=0,
        status=EventStatus.SUCCESS
        if event_type != EventType.STEP_START
        else EventStatus.STARTED,
        model_call=model_call,
        tool_call=tool_call,
        incident_id="checkout_timeout_wrong_tool",
    )


def _state_event(
    context: _EventContext,
    step_index: int,
    step_name: StepName,
    state_before: Dict[str, Any],
    state_after: Dict[str, Any],
    *,
    transition_label: str,
    state_patch: Dict[str, Any],
    changed_fields: Tuple[str, ...],
) -> TraceEvent:
    timestamp_start = context.timestamp()
    state_transition = StateTransitionPayload(
        state_before_hash=stable_hash(state_before),
        state_after_hash=stable_hash(state_after),
        state_patch=state_patch,
        transition_label=transition_label,
        protected_fields=V1_PROTECTED_FIELDS,
        changed_fields=changed_fields,
    )
    return TraceEvent(
        event_id=context.next_event_id(step_index, EventType.STATE_TRANSITION),
        trace_id=context.trace_id,
        run_id=context.run_id,
        step_index=step_index,
        step_name=step_name,
        event_type=EventType.STATE_TRANSITION,
        timestamp_start=timestamp_start,
        timestamp_end=timestamp_start,
        latency_ms=0,
        status=EventStatus.SUCCESS,
        state_transition=state_transition,
        incident_id="checkout_timeout_wrong_tool",
    )
