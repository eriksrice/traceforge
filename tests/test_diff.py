from traceforge.diff import compare_trace_events, extract_protected_snapshot
from traceforge.models import DivergenceLabel, DivergenceSeverity, ReplayStatus
from traceforge.workflow import run_workflow


def test_extract_protected_snapshot_finds_route_tool_and_classification() -> None:
    result = run_workflow("baseline", write_trace=False)

    snapshot = extract_protected_snapshot(result.events)

    assert snapshot.protected_values["step_1.output.requested_tool"] == "service_metrics_lookup"
    assert snapshot.protected_values["step_2.tool_name"] == "service_metrics_lookup"
    assert (
        snapshot.protected_values["step_3.output.incident_type"]
        == "service_regression_after_deploy"
    )


def test_compare_baseline_to_incident_marks_requested_tool_first() -> None:
    baseline = run_workflow("baseline", write_trace=False)
    incident = run_workflow("incident", write_trace=False)

    artifact = compare_trace_events(baseline.events, incident.events)

    assert artifact.replay_status == ReplayStatus.DIVERGED_UNACCEPTABLE
    assert artifact.first_divergence_field == "step_1.output.requested_tool"
    assert artifact.first_divergence_step_index == 1
    assert artifact.root_divergence_label == DivergenceLabel.TOOL_SELECTION_CHANGED

    first = [item for item in artifact.comparisons if item.first_divergence][0]
    assert first.baseline_value == "service_metrics_lookup"
    assert first.candidate_value == "billing_ledger_lookup"
    assert first.divergence_severity == DivergenceSeverity.BLOCKING


def test_compare_marks_later_differences_as_downstream() -> None:
    baseline = run_workflow("baseline", write_trace=False)
    incident = run_workflow("incident", write_trace=False)

    artifact = compare_trace_events(baseline.events, incident.events)
    downstream = {
        item.field_path: item
        for item in artifact.comparisons
        if item.downstream_of == "step_1.output.requested_tool"
    }

    assert "step_2.tool_name" in downstream
    assert "step_3.output.incident_type" in downstream
    assert downstream["step_3.output.severity"].divergence_severity == DivergenceSeverity.WARNING


def test_compare_baseline_to_patched_has_no_blocking_divergence() -> None:
    baseline = run_workflow("baseline", write_trace=False)
    patched = run_workflow("patched", write_trace=False)

    artifact = compare_trace_events(baseline.events, patched.events)

    assert artifact.replay_status == ReplayStatus.MATCHED
    assert artifact.first_divergence_field is None
    assert all(item.matched for item in artifact.comparisons)
