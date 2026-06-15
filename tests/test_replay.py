from traceforge.models import ReplayStatus
from traceforge.replay import compare_trace_files, read_comparison_artifact
from traceforge.workflow import run_workflow


def test_compare_trace_files_writes_artifact(tmp_path) -> None:
    trace_dir = tmp_path / "traces"
    baseline = run_workflow("baseline", output_dir=trace_dir)
    incident = run_workflow("incident", output_dir=trace_dir)
    output_path = trace_dir / "replay_baseline_vs_incident.json"

    artifact = compare_trace_files(
        baseline.trace_path,
        incident.trace_path,
        output_path=output_path,
    )
    loaded = read_comparison_artifact(output_path)

    assert artifact.first_divergence_field == "step_1.output.requested_tool"
    assert loaded.replay_status == ReplayStatus.DIVERGED_UNACCEPTABLE
    assert output_path.exists()
