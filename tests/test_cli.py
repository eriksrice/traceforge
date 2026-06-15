from typer.testing import CliRunner

from traceforge.cli import app
from traceforge.tracing import read_trace


def test_cli_run_writes_trace(tmp_path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["run", "--case", "baseline", "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0
    trace_path = tmp_path / "baseline_good.jsonl"
    assert trace_path.exists()
    assert len(read_trace(trace_path)) == 12


def test_cli_run_no_overwrite_reports_clean_error(tmp_path) -> None:
    runner = CliRunner()

    first = runner.invoke(
        app,
        ["run", "--case", "baseline", "--output-dir", str(tmp_path)],
    )
    second = runner.invoke(
        app,
        [
            "run",
            "--case",
            "baseline",
            "--output-dir",
            str(tmp_path),
            "--no-overwrite",
        ],
    )

    assert first.exit_code == 0
    assert second.exit_code == 1
    assert "trace already exists" in second.output


def test_cli_replay_writes_first_divergence_artifact(tmp_path) -> None:
    runner = CliRunner()
    trace_dir = tmp_path / "traces"
    output_path = trace_dir / "comparison.json"

    runner.invoke(app, ["run", "--case", "baseline", "--output-dir", str(trace_dir)])
    runner.invoke(app, ["run", "--case", "incident", "--output-dir", str(trace_dir)])
    result = runner.invoke(
        app,
        [
            "replay",
            "--baseline",
            str(trace_dir / "baseline_good.jsonl"),
            "--candidate",
            str(trace_dir / "incident_bad.jsonl"),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    assert "first_divergence=step_1.output.requested_tool" in result.output


def test_cli_gate_passes_and_writes_artifacts(tmp_path) -> None:
    runner = CliRunner()
    trace_dir = tmp_path / "traces"
    report_dir = tmp_path / "reports"

    result = runner.invoke(
        app,
        [
            "gate",
            "--trace-dir",
            str(trace_dir),
            "--report-dir",
            str(report_dir),
        ],
    )

    assert result.exit_code == 0
    assert "gate_status=pass" in result.output
    assert (trace_dir / "regression_gate_result.json").exists()
    assert (report_dir / "regression_gate_report.md").exists()


def test_cli_report_commands_regenerate_markdown(tmp_path) -> None:
    runner = CliRunner()
    trace_dir = tmp_path / "traces"
    report_dir = tmp_path / "reports"

    runner.invoke(app, ["run", "--case", "baseline", "--output-dir", str(trace_dir)])
    runner.invoke(app, ["run", "--case", "incident", "--output-dir", str(trace_dir)])
    replay_result = runner.invoke(
        app,
        [
            "replay",
            "--baseline",
            str(trace_dir / "baseline_good.jsonl"),
            "--candidate",
            str(trace_dir / "incident_bad.jsonl"),
            "--output",
            str(trace_dir / "comparison.json"),
        ],
    )

    first_result = runner.invoke(
        app,
        [
            "report",
            "first-divergence",
            "--comparison",
            str(trace_dir / "comparison.json"),
            "--output",
            str(report_dir / "first_divergence_report.md"),
        ],
    )
    timeline_result = runner.invoke(
        app,
        [
            "report",
            "timeline",
            "--baseline",
            str(trace_dir / "baseline_good.jsonl"),
            "--trace",
            str(trace_dir / "incident_bad.jsonl"),
            "--comparison",
            str(trace_dir / "comparison.json"),
            "--output",
            str(report_dir / "incident_timeline.md"),
        ],
    )

    assert replay_result.exit_code == 0
    assert first_result.exit_code == 0
    assert timeline_result.exit_code == 0
    assert "first_divergence_report.md" in first_result.output
    assert "incident_timeline.md" in timeline_result.output
    assert (report_dir / "first_divergence_report.md").exists()
    assert (report_dir / "incident_timeline.md").exists()
