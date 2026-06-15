"""Fixture loading for cached model outputs and mocked tool responses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field, model_validator

from traceforge.hashing import stable_hash
from traceforge.models import (
    ModelOutputMode,
    StepName,
    ToolReplayMode,
    ToolStatus,
    TraceForgeModel,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INCIDENT_FIXTURE = "fixtures/incidents/checkout_timeout_input.json"
DEFAULT_FIXTURE_VERSION = "v1"


class FixtureLoadError(ValueError):
    """Raised when fixture files fail TraceForge contract checks."""


class IncidentCaseExpectation(TraceForgeModel):
    """Expected fixture paths and protected values for one case."""

    prompt_version: str = Field(min_length=1)
    route_fixture: str = Field(min_length=1)
    tool_fixture: str = Field(min_length=1)
    classification_fixture: str = Field(min_length=1)
    protected_expectations: Dict[str, Any]


class IncidentFixture(TraceForgeModel):
    """The synthetic incident input and case contract."""

    case_id: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source: str = Field(min_length=1)
    customer: Dict[str, Any]
    alert: Dict[str, Any]
    known_release_context: Dict[str, Any]
    workflow: Dict[str, Any]
    expected_cases: Dict[str, IncidentCaseExpectation]
    first_divergence_contract: Dict[str, Any]
    notes: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def required_cases_exist(self) -> "IncidentFixture":
        missing = {"baseline", "incident", "patched"} - set(self.expected_cases)
        if missing:
            raise ValueError(f"incident fixture missing expected cases: {sorted(missing)}")
        return self


class ModelOutputFixture(TraceForgeModel):
    """Cached or synthetic model output fixture."""

    fixture_id: str = Field(min_length=1)
    fixture_version: str = Field(min_length=1)
    fixture_type: str = Field(pattern="^model_output$")
    case_id: str = Field(min_length=1)
    step_index: int = Field(ge=1, le=3)
    step_name: StepName
    prompt_id: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    model_provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    model_output_mode: ModelOutputMode
    input_ref: str = Field(min_length=1)
    output: Dict[str, Any]

    @model_validator(mode="after")
    def route_and_classification_steps_only(self) -> "ModelOutputFixture":
        if self.step_name == StepName.INTAKE_ROUTE and self.step_index != 1:
            raise ValueError("intake_route fixtures must use step_index 1")
        if self.step_name == StepName.CLASSIFY_INCIDENT and self.step_index != 3:
            raise ValueError("classify_incident fixtures must use step_index 3")
        if self.model_output_mode == ModelOutputMode.LIVE:
            raise ValueError("v1 fixtures cannot use live model output mode")
        return self


class ToolOutputFixture(TraceForgeModel):
    """Mocked tool output fixture."""

    fixture_id: str = Field(min_length=1)
    fixture_version: str = Field(min_length=1)
    fixture_type: str = Field(pattern="^tool_output$")
    case_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    tool_version: str = Field(min_length=1)
    tool_replay_mode: ToolReplayMode
    tool_status: ToolStatus
    latency_ms: int = Field(ge=0)
    input: Dict[str, Any]
    output: Dict[str, Any]

    @model_validator(mode="after")
    def tool_must_be_mocked(self) -> "ToolOutputFixture":
        if self.tool_replay_mode != ToolReplayMode.MOCKED:
            raise ValueError("v1 tool fixtures must use mocked replay mode")
        if self.tool_status != ToolStatus.SUCCESS:
            raise ValueError("v1 tool fixtures currently cover successful responses only")
        return self


class CaseFixtures(TraceForgeModel):
    """Loaded fixture set for one baseline, incident, or patched case."""

    case_name: str = Field(min_length=1)
    incident: IncidentFixture
    route: ModelOutputFixture
    tool: ToolOutputFixture
    classification: ModelOutputFixture


def resolve_fixture_path(relative_path: str, *, root: Optional[Path] = None) -> Path:
    """Resolve a repository-relative fixture path."""

    base = root or REPO_ROOT
    return (base / relative_path).resolve()


def load_json_fixture(relative_path: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    """Load a JSON fixture from a repository-relative path."""

    path = resolve_fixture_path(relative_path, root=root)
    if not path.exists():
        raise FixtureLoadError(f"fixture not found: {relative_path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _check_version(fixture_id: str, actual: str, expected: str) -> None:
    if actual != expected:
        raise FixtureLoadError(
            f"fixture {fixture_id} has version {actual}, expected {expected}"
        )


def load_incident_fixture(
    relative_path: str = DEFAULT_INCIDENT_FIXTURE,
    *,
    root: Optional[Path] = None,
) -> IncidentFixture:
    """Load the incident input and case expectations."""

    return IncidentFixture.model_validate(load_json_fixture(relative_path, root=root))


def load_model_output_fixture(
    relative_path: str,
    *,
    expected_version: str = DEFAULT_FIXTURE_VERSION,
    root: Optional[Path] = None,
) -> ModelOutputFixture:
    """Load and validate a cached model output fixture."""

    fixture = ModelOutputFixture.model_validate(load_json_fixture(relative_path, root=root))
    _check_version(fixture.fixture_id, fixture.fixture_version, expected_version)
    return fixture


def load_tool_output_fixture(
    relative_path: str,
    *,
    expected_version: str = DEFAULT_FIXTURE_VERSION,
    root: Optional[Path] = None,
) -> ToolOutputFixture:
    """Load and validate a mocked tool output fixture."""

    fixture = ToolOutputFixture.model_validate(load_json_fixture(relative_path, root=root))
    _check_version(fixture.fixture_id, fixture.fixture_version, expected_version)
    return fixture


def load_case_fixtures(
    case_name: str,
    *,
    incident_path: str = DEFAULT_INCIDENT_FIXTURE,
    expected_version: str = DEFAULT_FIXTURE_VERSION,
    root: Optional[Path] = None,
) -> CaseFixtures:
    """Load incident, route, tool, and classification fixtures for one case."""

    incident = load_incident_fixture(incident_path, root=root)
    if case_name not in incident.expected_cases:
        raise FixtureLoadError(f"unknown case {case_name!r}")

    expected = incident.expected_cases[case_name]
    route = load_model_output_fixture(
        expected.route_fixture, expected_version=expected_version, root=root
    )
    tool = load_tool_output_fixture(
        expected.tool_fixture, expected_version=expected_version, root=root
    )
    classification = load_model_output_fixture(
        expected.classification_fixture,
        expected_version=expected_version,
        root=root,
    )

    _validate_case_contract(case_name, incident, expected, route, tool, classification)
    return CaseFixtures(
        case_name=case_name,
        incident=incident,
        route=route,
        tool=tool,
        classification=classification,
    )


def fixture_hash(fixture: TraceForgeModel) -> str:
    """Hash a validated fixture model deterministically."""

    return stable_hash(fixture.model_dump(mode="json"))


def _validate_case_contract(
    case_name: str,
    incident: IncidentFixture,
    expected: IncidentCaseExpectation,
    route: ModelOutputFixture,
    tool: ToolOutputFixture,
    classification: ModelOutputFixture,
) -> None:
    fixtures = (route, tool, classification)
    for fixture in fixtures:
        if fixture.case_id != incident.case_id:
            raise FixtureLoadError(
                f"{case_name} fixture case_id {fixture.case_id!r} does not match "
                f"incident case_id {incident.case_id!r}"
            )

    if route.prompt_version != expected.prompt_version:
        raise FixtureLoadError(
            f"{case_name} route prompt {route.prompt_version!r} does not match "
            f"expected {expected.prompt_version!r}"
        )

    protected = expected.protected_expectations
    _assert_output_value(case_name, "requested_tool", route.output, protected)
    _assert_output_value(case_name, "diagnostic_route", route.output, protected)
    _assert_output_value(case_name, "evidence_family", tool.output, protected)
    _assert_output_value(case_name, "incident_type", classification.output, protected)
    _assert_output_value(case_name, "severity", classification.output, protected)
    _assert_output_value(
        case_name, "escalation_required", classification.output, protected
    )


def _assert_output_value(
    case_name: str,
    field_name: str,
    output: Dict[str, Any],
    expected: Dict[str, Any],
) -> None:
    if field_name not in expected:
        raise FixtureLoadError(f"{case_name} missing protected expectation {field_name}")
    if output.get(field_name) != expected[field_name]:
        raise FixtureLoadError(
            f"{case_name} fixture field {field_name}={output.get(field_name)!r} "
            f"does not match expected {expected[field_name]!r}"
        )
