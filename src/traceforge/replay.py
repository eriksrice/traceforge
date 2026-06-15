"""Deterministic replay comparison harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from traceforge.diff import TraceComparisonArtifact, compare_trace_events
from traceforge.models import ReplayMode
from traceforge.tracing import read_trace

DEFAULT_INCIDENT_COMPARISON = Path("traces/replay_baseline_vs_incident.json")


def compare_trace_files(
    baseline_path: Path,
    candidate_path: Path,
    *,
    output_path: Optional[Path] = None,
    replay_mode: ReplayMode = ReplayMode.INCIDENT,
    overwrite: bool = True,
) -> TraceComparisonArtifact:
    """Compare two trace files and optionally write the comparison artifact."""

    baseline_events = read_trace(baseline_path)
    candidate_events = read_trace(candidate_path)
    artifact = compare_trace_events(
        baseline_events,
        candidate_events,
        replay_mode=replay_mode,
    )

    if output_path is not None:
        write_comparison_artifact(artifact, output_path, overwrite=overwrite)

    return artifact


def write_comparison_artifact(
    artifact: TraceComparisonArtifact,
    output_path: Path,
    *,
    overwrite: bool = True,
) -> Path:
    """Write a replay comparison artifact as stable pretty JSON."""

    if output_path.exists() and not overwrite:
        raise FileExistsError(f"comparison artifact already exists: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if overwrite else "x"
    with output_path.open(mode, encoding="utf-8") as handle:
        json.dump(artifact.model_dump(mode="json"), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path


def read_comparison_artifact(path: Path) -> TraceComparisonArtifact:
    """Read a replay comparison artifact."""

    with path.open("r", encoding="utf-8") as handle:
        return TraceComparisonArtifact.model_validate(json.load(handle))
