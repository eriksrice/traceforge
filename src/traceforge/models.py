"""Typed contracts for TraceForge traces, replay comparisons, and gates."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TRACE_SCHEMA_VERSION = "traceforge.trace_event.v1"
STATE_SCHEMA_VERSION = "traceforge.workflow_state.v1"

V1_STEP_NAMES = ("intake_route", "collect_evidence", "classify_incident")

V1_PROTECTED_FIELDS = (
    "step_1.output.requested_tool",
    "step_1.output.diagnostic_route",
    "step_1.state.transition_label",
    "step_2.tool_name",
    "step_2.output.evidence_family",
    "step_2.state.transition_label",
    "step_3.output.incident_type",
    "step_3.output.severity",
    "step_3.output.engineering_next_action",
    "step_3.output.escalation_required",
    "step_3.state.transition_label",
    "trace.schema_valid",
)

V1_ALLOWED_VOLATILE_FIELDS = (
    "event_id",
    "timestamp_start",
    "timestamp_end",
    "latency_ms",
    "tool_latency_ms",
    "estimated_cost_usd",
    "token_input_count",
    "token_output_count",
)


class TraceForgeModel(BaseModel):
    """Base model with strict field names and enum serialization."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class EventType(str, Enum):
    STEP_START = "step_start"
    MODEL_CALL = "model_call"
    TOOL_CALL = "tool_call"
    STATE_TRANSITION = "state_transition"
    STEP_END = "step_end"
    REPLAY_COMPARISON = "replay_comparison"
    GATE_RESULT = "gate_result"


class EventStatus(str, Enum):
    STARTED = "started"
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"
    REPLAYED = "replayed"


class StepName(str, Enum):
    INTAKE_ROUTE = "intake_route"
    COLLECT_EVIDENCE = "collect_evidence"
    CLASSIFY_INCIDENT = "classify_incident"


class ModelOutputMode(str, Enum):
    CACHED = "cached"
    SYNTHETIC = "synthetic"
    LIVE = "live"


class ToolStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class ToolReplayMode(str, Enum):
    MOCKED = "mocked"
    LIVE = "live"
    SKIPPED = "skipped"


class ReplayMode(str, Enum):
    ORIGINAL = "original"
    INCIDENT = "incident"
    PATCHED = "patched"


class ReplayStatus(str, Enum):
    MATCHED = "matched"
    DIVERGED_ALLOWED = "diverged_allowed"
    DIVERGED_UNACCEPTABLE = "diverged_unacceptable"
    NOT_REPLAYABLE = "not_replayable"


class DeterminismClass(str, Enum):
    DETERMINISTIC = "deterministic"
    STOCHASTIC_STABLE = "stochastic_stable"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class DivergenceLabel(str, Enum):
    NONE = "none"
    ALLOWED_NONDETERMINISTIC = "allowed_nondeterministic"
    PROMPT_OUTPUT_CHANGED = "prompt_output_changed"
    TOOL_SELECTION_CHANGED = "tool_selection_changed"
    TOOL_RESPONSE_CHANGED = "tool_response_changed"
    STATE_TRANSITION_CHANGED = "state_transition_changed"
    SCHEMA_VIOLATION = "schema_violation"
    MISSING_EVENT = "missing_event"
    UNEXPECTED_ERROR = "unexpected_error"


class DivergenceSeverity(str, Enum):
    NONE = "none"
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


class GateStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


class ProtectedFieldSpec(TraceForgeModel):
    """A field whose value can block release-gate success."""

    path: str = Field(min_length=1)
    description: str = Field(min_length=1)
    required: bool = True


class ModelCallPayload(TraceForgeModel):
    """Prompt and model metadata for a cached, synthetic, or live model call."""

    model_provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    temperature: Optional[float] = Field(default=None, ge=0)
    seed: Optional[int] = None
    prompt_id: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    prompt_hash: str = Field(min_length=1)
    system_prompt_hash: Optional[str] = None
    input_hash: str = Field(min_length=1)
    output_hash: str = Field(min_length=1)
    token_input_count: Optional[int] = Field(default=None, ge=0)
    token_output_count: Optional[int] = Field(default=None, ge=0)
    estimated_cost_usd: Optional[float] = Field(default=None, ge=0)
    model_output_mode: ModelOutputMode
    model_fixture_id: Optional[str] = None
    model_fixture_version: Optional[str] = None

    @model_validator(mode="after")
    def cached_outputs_need_fixture(self) -> "ModelCallPayload":
        if self.model_output_mode in {ModelOutputMode.CACHED, ModelOutputMode.SYNTHETIC}:
            if not self.model_fixture_id or not self.model_fixture_version:
                raise ValueError("cached/synthetic model outputs require fixture id and version")
        return self


class ToolCallPayload(TraceForgeModel):
    """Tool call metadata and mocked response contract."""

    tool_name: str = Field(min_length=1)
    tool_version: str = Field(min_length=1)
    tool_call_id: str = Field(min_length=1)
    tool_input: dict[str, Any]
    tool_input_hash: str = Field(min_length=1)
    tool_output: Optional[dict[str, Any]] = None
    tool_output_hash: Optional[str] = None
    tool_latency_ms: Optional[int] = Field(default=None, ge=0)
    tool_status: ToolStatus
    tool_error_type: Optional[str] = None
    tool_fixture_id: Optional[str] = None
    tool_fixture_version: Optional[str] = None
    tool_replay_mode: ToolReplayMode

    @model_validator(mode="after")
    def mocked_tools_need_fixture(self) -> "ToolCallPayload":
        if self.tool_replay_mode == ToolReplayMode.MOCKED:
            if not self.tool_fixture_id or not self.tool_fixture_version:
                raise ValueError("mocked tool replay requires fixture id and version")
        if self.tool_status == ToolStatus.SUCCESS and self.tool_output is None:
            raise ValueError("successful tool calls require tool_output")
        return self


class StateTransitionPayload(TraceForgeModel):
    """State transition metadata for replayable workflow behavior."""

    state_before_hash: str = Field(min_length=1)
    state_after_hash: str = Field(min_length=1)
    state_patch: dict[str, Any]
    state_schema_version: str = STATE_SCHEMA_VERSION
    transition_label: str = Field(min_length=1)
    protected_fields: tuple[str, ...] = Field(default_factory=tuple)
    changed_fields: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("state_schema_version")
    @classmethod
    def state_schema_must_be_v1(cls, value: str) -> str:
        if value != STATE_SCHEMA_VERSION:
            raise ValueError(f"state_schema_version must be {STATE_SCHEMA_VERSION}")
        return value


class Divergence(TraceForgeModel):
    """A single field-level replay comparison result."""

    field_path: str = Field(min_length=1)
    baseline_value: Any = None
    candidate_value: Any = None
    divergence_label: DivergenceLabel = DivergenceLabel.NONE
    divergence_severity: DivergenceSeverity = DivergenceSeverity.NONE
    first_divergence: bool = False
    allowed_divergence_reason: Optional[str] = None

    @model_validator(mode="after")
    def blocking_divergence_needs_label(self) -> "Divergence":
        if self.divergence_severity == DivergenceSeverity.BLOCKING:
            if self.divergence_label == DivergenceLabel.NONE:
                raise ValueError("blocking divergence must have a non-none label")
            if self.allowed_divergence_reason is not None:
                raise ValueError("blocking divergence cannot have an allowed reason")
        return self


class ReplayComparison(TraceForgeModel):
    """Comparison of one baseline event against one replay/candidate event."""

    baseline_event_id: str = Field(min_length=1)
    replay_event_id: str = Field(min_length=1)
    replay_mode: ReplayMode
    replay_status: ReplayStatus
    determinism_class: DeterminismClass
    divergence_label: DivergenceLabel = DivergenceLabel.NONE
    divergence_severity: DivergenceSeverity = DivergenceSeverity.NONE
    first_divergence: bool = False
    root_divergence_event_id: Optional[str] = None
    allowed_divergence_reason: Optional[str] = None
    divergences: tuple[Divergence, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def unacceptable_divergence_needs_root(self) -> "ReplayComparison":
        if self.replay_status == ReplayStatus.DIVERGED_UNACCEPTABLE:
            if self.divergence_severity == DivergenceSeverity.NONE:
                raise ValueError("unacceptable divergence needs non-none severity")
            if self.divergence_label == DivergenceLabel.NONE:
                raise ValueError("unacceptable divergence needs non-none label")
        if self.first_divergence and not self.root_divergence_event_id:
            raise ValueError("first divergence comparisons require root_divergence_event_id")
        return self


class GateResult(TraceForgeModel):
    """CI-style regression gate result."""

    gate_name: str = Field(min_length=1)
    gate_status: GateStatus
    incident_id: str = Field(min_length=1)
    checked_traces: tuple[str, ...] = Field(default_factory=tuple)
    checked_reports: tuple[str, ...] = Field(default_factory=tuple)
    blocking_reasons: tuple[str, ...] = Field(default_factory=tuple)
    review_required: bool = False
    notes: str = ""

    @model_validator(mode="after")
    def failed_gates_need_blocking_reasons(self) -> "GateResult":
        if self.gate_status == GateStatus.FAIL and not self.blocking_reasons:
            raise ValueError("failed gates require at least one blocking reason")
        return self


class TraceEvent(TraceForgeModel):
    """One append-only JSONL trace event."""

    event_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    parent_event_id: Optional[str] = None
    step_index: int = Field(ge=1, le=3)
    step_name: StepName
    event_type: EventType
    timestamp_start: datetime
    timestamp_end: Optional[datetime] = None
    latency_ms: Optional[int] = Field(default=None, ge=0)
    status: EventStatus
    schema_version: str = TRACE_SCHEMA_VERSION
    model_call: Optional[ModelCallPayload] = None
    tool_call: Optional[ToolCallPayload] = None
    state_transition: Optional[StateTransitionPayload] = None
    replay_comparison: Optional[ReplayComparison] = None
    gate_result: Optional[GateResult] = None
    incident_id: Optional[str] = None
    decision_record_id: Optional[str] = None
    release_candidate_id: Optional[str] = None
    review_required: bool = False
    notes: str = ""

    @field_validator("schema_version")
    @classmethod
    def trace_schema_must_be_v1(cls, value: str) -> str:
        if value != TRACE_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {TRACE_SCHEMA_VERSION}")
        return value

    @model_validator(mode="after")
    def event_type_matches_payload(self) -> "TraceEvent":
        if self.event_type == EventType.MODEL_CALL and self.model_call is None:
            raise ValueError("model_call events require model_call payload")
        if self.event_type == EventType.TOOL_CALL and self.tool_call is None:
            raise ValueError("tool_call events require tool_call payload")
        if self.event_type == EventType.STATE_TRANSITION and self.state_transition is None:
            raise ValueError("state_transition events require state_transition payload")
        if self.event_type == EventType.REPLAY_COMPARISON and self.replay_comparison is None:
            raise ValueError("replay_comparison events require replay_comparison payload")
        if self.event_type == EventType.GATE_RESULT and self.gate_result is None:
            raise ValueError("gate_result events require gate_result payload")
        if self.timestamp_end and self.timestamp_end < self.timestamp_start:
            raise ValueError("timestamp_end cannot be before timestamp_start")
        return self
