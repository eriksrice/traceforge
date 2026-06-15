# TraceForge Architecture

TraceForge v1 is a deterministic, file-backed incident replay system for one LLM/tool workflow.

## Components

- Typed trace event contracts.
- Stable hashing for inputs, outputs, prompts, tools, and state.
- Cached model-output fixtures.
- Mocked tool-response fixtures.
- A 3-step incident triage workflow.
- Append-only JSONL trace writing.
- Replay comparison against protected fields.
- First-divergence classification.
- Trace-derived reports.
- CI-style gate behavior.

## V1 Boundary

The first build uses plain Python modules, Pydantic contracts, file artifacts, and Typer entry points. It does not use LangGraph, live model providers, external services, dashboards, vector databases, or broad platform abstractions.
