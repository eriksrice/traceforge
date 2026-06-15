"""Command-line entry point for TraceForge."""

from __future__ import annotations

from pathlib import Path

import typer

from traceforge.gate import run_gate
from traceforge.models import GateStatus
from traceforge.replay import (
    DEFAULT_INCIDENT_COMPARISON,
    compare_trace_files,
    read_comparison_artifact,
)
from traceforge.reports import (
    FIRST_DIVERGENCE_REPORT,
    INCIDENT_TIMELINE_REPORT,
    write_first_divergence_report,
    write_incident_timeline_report,
)
from traceforge.tracing import TraceWriteError, read_trace
from traceforge.workflow import CASE_TRACE_FILES, run_workflow

app = typer.Typer(help="TraceForge incident replay commands.")
report_app = typer.Typer(help="Regenerate trace-derived markdown reports.")


@app.command("run")
def run_case(
    case: str = typer.Option(..., "--case", help="Case to run: baseline, incident, or patched."),
    output_dir: Path = typer.Option(
        Path("traces"),
        "--output-dir",
        help="Directory for generated JSONL trace artifacts.",
    ),
    overwrite: bool = typer.Option(
        True,
        "--overwrite/--no-overwrite",
        help="Overwrite the case trace file if it already exists.",
    ),
) -> None:
    """Run one deterministic fixture-backed workflow case."""

    if case not in CASE_TRACE_FILES:
        allowed = ", ".join(sorted(CASE_TRACE_FILES))
        raise typer.BadParameter(f"unknown case {case!r}; expected one of: {allowed}")

    try:
        result = run_workflow(case, output_dir=output_dir, overwrite=overwrite)
    except TraceWriteError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(str(result.trace_path))


@app.command("replay")
def replay_traces(
    baseline: Path = typer.Option(
        ...,
        "--baseline",
        help="Baseline JSONL trace to compare from.",
    ),
    candidate: Path = typer.Option(
        ...,
        "--candidate",
        help="Candidate JSONL trace to compare against the baseline.",
    ),
    output: Path = typer.Option(
        DEFAULT_INCIDENT_COMPARISON,
        "--output",
        help="Path for the generated replay comparison JSON artifact.",
    ),
    overwrite: bool = typer.Option(
        True,
        "--overwrite/--no-overwrite",
        help="Overwrite the comparison artifact if it already exists.",
    ),
) -> None:
    """Compare two traces and write a first-divergence artifact."""

    try:
        artifact = compare_trace_files(
            baseline,
            candidate,
            output_path=output,
            overwrite=overwrite,
        )
    except FileExistsError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(str(output))
    if artifact.first_divergence_field:
        typer.echo(f"first_divergence={artifact.first_divergence_field}")


@report_app.command("first-divergence")
def report_first_divergence(
    comparison: Path = typer.Option(
        DEFAULT_INCIDENT_COMPARISON,
        "--comparison",
        help="Replay comparison JSON artifact to summarize.",
    ),
    output: Path = typer.Option(
        FIRST_DIVERGENCE_REPORT,
        "--output",
        help="Path for the generated markdown report.",
    ),
) -> None:
    """Regenerate the first-divergence markdown report."""

    artifact = read_comparison_artifact(comparison)
    report_path = write_first_divergence_report(artifact, output)
    typer.echo(str(report_path))


@report_app.command("timeline")
def report_timeline(
    trace: Path = typer.Option(
        Path("traces/incident_bad.jsonl"),
        "--trace",
        help="Incident JSONL trace to reconstruct.",
    ),
    comparison: Path = typer.Option(
        DEFAULT_INCIDENT_COMPARISON,
        "--comparison",
        help="Replay comparison JSON artifact for first-divergence evidence.",
    ),
    baseline: Path = typer.Option(
        Path("traces/baseline_good.jsonl"),
        "--baseline",
        help="Baseline JSONL trace used for comparison context.",
    ),
    output: Path = typer.Option(
        INCIDENT_TIMELINE_REPORT,
        "--output",
        help="Path for the generated markdown report.",
    ),
) -> None:
    """Regenerate the incident timeline markdown report."""

    artifact = read_comparison_artifact(comparison)
    report_path = write_incident_timeline_report(
        read_trace(baseline),
        read_trace(trace),
        artifact,
        output,
    )
    typer.echo(str(report_path))


@app.command("gate")
def gate(
    trace_dir: Path = typer.Option(
        Path("traces"),
        "--trace-dir",
        help="Directory for trace and comparison artifacts.",
    ),
    report_dir: Path = typer.Option(
        Path("reports"),
        "--report-dir",
        help="Directory for generated markdown reports.",
    ),
    overwrite: bool = typer.Option(
        True,
        "--overwrite/--no-overwrite",
        help="Overwrite generated gate artifacts.",
    ),
) -> None:
    """Run the seeded CI-style regression gate."""

    result = run_gate(trace_dir=trace_dir, report_dir=report_dir, overwrite=overwrite)
    typer.echo(f"gate_status={result.gate_status}")
    if result.blocking_reasons:
        for reason in result.blocking_reasons:
            typer.echo(f"blocking_reason={reason}")
    raise typer.Exit(code=0 if result.gate_status == GateStatus.PASS else 1)


app.add_typer(report_app, name="report")


@app.callback()
def main() -> None:
    """TraceForge CLI."""
