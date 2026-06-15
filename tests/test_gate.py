import json

from traceforge.gate import run_gate
from traceforge.replay import read_comparison_artifact


def test_gate_passes_when_bad_fails_and_patched_matches(tmp_path) -> None:
    trace_dir = tmp_path / "traces"
    report_dir = tmp_path / "reports"

    result = run_gate(trace_dir=trace_dir, report_dir=report_dir)

    assert result.gate_status == "pass"
    assert result.blocking_reasons == ()
    assert (trace_dir / "patched_good.jsonl").exists()
    assert (trace_dir / "replay_baseline_vs_patched.json").exists()
    assert (trace_dir / "regression_gate_result.json").exists()

    incident = read_comparison_artifact(trace_dir / "replay_baseline_vs_incident.json")
    patched = read_comparison_artifact(trace_dir / "replay_baseline_vs_patched.json")
    assert incident.first_divergence_field == "step_1.output.requested_tool"
    assert patched.replay_status == "matched"
    assert patched.first_divergence_field is None

    with (trace_dir / "regression_gate_result.json").open("r", encoding="utf-8") as handle:
        saved = json.load(handle)
    assert saved["gate_status"] == "pass"
