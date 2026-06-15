from traceforge.models import EventType, StepName
from traceforge.workflow import build_trace_events, load_case_fixtures, run_workflow


def test_baseline_workflow_emits_three_steps_in_order() -> None:
    fixtures = load_case_fixtures("baseline")
    events, final_state = build_trace_events(
        fixtures,
        trace_id="trace_test_baseline",
        run_id="baseline_good",
    )

    assert len(events) == 12
    assert [event.step_index for event in events] == [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
    assert {event.step_name for event in events} == {
        StepName.INTAKE_ROUTE,
        StepName.COLLECT_EVIDENCE,
        StepName.CLASSIFY_INCIDENT,
    }
    assert final_state["requested_tool"] == "service_metrics_lookup"
    assert final_state["incident_type"] == "service_regression_after_deploy"


def test_incident_workflow_reproduces_wrong_tool_selection() -> None:
    result = run_workflow("incident", write_trace=False)

    model_events = [event for event in result.events if event.event_type == EventType.MODEL_CALL]
    tool_events = [event for event in result.events if event.event_type == EventType.TOOL_CALL]

    assert result.final_state["requested_tool"] == "billing_ledger_lookup"
    assert result.final_state["incident_type"] == "account_billing_configuration_issue"
    assert model_events[0].model_call.output_hash
    assert tool_events[0].tool_call.tool_name == "billing_ledger_lookup"
    assert tool_events[0].tool_call.tool_replay_mode == "mocked"


def test_patched_workflow_matches_baseline_protected_fields() -> None:
    baseline = run_workflow("baseline", write_trace=False)
    patched = run_workflow("patched", write_trace=False)

    for field in [
        "requested_tool",
        "diagnostic_route",
        "evidence_family",
        "incident_type",
        "severity",
        "engineering_next_action",
        "escalation_required",
    ]:
        assert patched.final_state[field] == baseline.final_state[field]
