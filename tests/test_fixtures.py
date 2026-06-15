import json
from pathlib import Path

import pytest

from traceforge.fixtures import (
    FixtureLoadError,
    fixture_hash,
    load_case_fixtures,
    load_incident_fixture,
    load_model_output_fixture,
    load_tool_output_fixture,
)


def test_incident_fixture_declares_required_cases() -> None:
    incident = load_incident_fixture()

    assert set(incident.expected_cases) == {"baseline", "incident", "patched"}
    assert incident.case_id == "checkout_timeout_wrong_tool"


def test_baseline_case_loads_expected_route_and_tool() -> None:
    case = load_case_fixtures("baseline")

    assert case.route.output["requested_tool"] == "service_metrics_lookup"
    assert case.tool.output["evidence_family"] == "service_telemetry"
    assert case.classification.output["incident_type"] == "service_regression_after_deploy"


def test_incident_case_loads_wrong_but_plausible_route() -> None:
    case = load_case_fixtures("incident")

    assert case.route.output["requested_tool"] == "billing_ledger_lookup"
    assert case.tool.output["ledger_status"] == "healthy"
    assert case.classification.output["escalation_required"] is False


def test_patched_case_matches_baseline_protected_fields() -> None:
    baseline = load_case_fixtures("baseline")
    patched = load_case_fixtures("patched")

    protected_fields = [
        "requested_tool",
        "diagnostic_route",
    ]
    for field in protected_fields:
        assert patched.route.output[field] == baseline.route.output[field]

    assert patched.classification.output["incident_type"] == baseline.classification.output["incident_type"]
    assert patched.classification.output["severity"] == baseline.classification.output["severity"]
    assert (
        patched.classification.output["escalation_required"]
        == baseline.classification.output["escalation_required"]
    )


def test_fixture_hash_is_stable() -> None:
    first = load_case_fixtures("baseline")
    second = load_case_fixtures("baseline")

    assert fixture_hash(first.route) == fixture_hash(second.route)


def test_unknown_case_is_rejected() -> None:
    with pytest.raises(FixtureLoadError):
        load_case_fixtures("missing")


def test_wrong_fixture_version_is_rejected() -> None:
    with pytest.raises(FixtureLoadError):
        load_model_output_fixture(
            "fixtures/model_outputs/baseline_good_route.json",
            expected_version="v2",
        )


def test_tool_fixture_loads_mocked_response() -> None:
    fixture = load_tool_output_fixture(
        "fixtures/tool_outputs/service_metrics_lookup_checkout_latency.json"
    )

    assert fixture.tool_name == "service_metrics_lookup"
    assert fixture.tool_replay_mode == "mocked"


def test_all_fixture_json_files_parse() -> None:
    fixture_root = Path("fixtures")
    for path in fixture_root.rglob("*.json"):
        with path.open("r", encoding="utf-8") as handle:
            assert json.load(handle)
