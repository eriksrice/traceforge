from traceforge.gate import run_gate


def test_gate_generates_markdown_reports(tmp_path) -> None:
    trace_dir = tmp_path / "traces"
    report_dir = tmp_path / "reports"

    result = run_gate(trace_dir=trace_dir, report_dir=report_dir)

    assert result.gate_status == "pass"
    first = report_dir / "first_divergence_report.md"
    timeline = report_dir / "incident_timeline.md"
    gate = report_dir / "regression_gate_report.md"
    assert first.exists()
    assert timeline.exists()
    assert gate.exists()
    assert "step_1.output.requested_tool" in first.read_text(encoding="utf-8")
    assert "billing_ledger_lookup" in timeline.read_text(encoding="utf-8")
    assert "Status: `pass`" in gate.read_text(encoding="utf-8")
