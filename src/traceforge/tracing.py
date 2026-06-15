"""Trace capture helpers and append-only event writing."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from traceforge.models import TraceEvent


class TraceWriteError(ValueError):
    """Raised when a trace cannot be written safely."""


class TraceWriter:
    """Append typed trace events to a JSONL trace artifact."""

    def __init__(self, path: Path, *, overwrite: bool = False) -> None:
        self.path = path
        self.overwrite = overwrite

    def write_events(self, events: Iterable[TraceEvent]) -> Path:
        """Write events as newline-delimited JSON and return the trace path."""

        event_list = list(events)
        if not event_list:
            raise TraceWriteError("cannot write an empty trace")
        if self.path.exists() and not self.overwrite:
            raise TraceWriteError(f"trace already exists: {self.path}")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        mode = "w" if self.overwrite else "x"
        with self.path.open(mode, encoding="utf-8") as handle:
            for event in event_list:
                handle.write(event.model_dump_json(exclude_none=False))
                handle.write("\n")
        return self.path


def read_trace(path: Path) -> List[TraceEvent]:
    """Read a JSONL trace artifact into typed events."""

    events: List[TraceEvent] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                events.append(TraceEvent.model_validate_json(stripped))
    return events
