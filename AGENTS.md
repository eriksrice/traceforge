# TraceForge Codex Guidance

## Project Identity

TraceForge is a file-backed incident replay system for LLM/tool pipelines. It captures typed traces, deterministically replays seeded incidents, detects first divergent steps, and turns fixes into CI-style regression gates.

This is a standalone portfolio project repository. It is separate from Erik Agent OS.

## Senior Hiring Signal

TraceForge should signal production AI reliability work, not another agent demo. Prioritize evidence of:

- Production AI reliability.
- Trace instrumentation.
- Deterministic replay.
- Mocked tool contracts.
- First-divergence classification.
- Incident reconstruction.
- Release gating.

The project should show that an LLM incident can be captured as a replayable operational artifact, compared against a known-good baseline, explained at the step level, and converted into a regression gate.

## V1 Scope

Keep v1 narrow and complete:

- One 3-step tool-using workflow.
- One typed trace event schema.
- One file-backed append-only trace store.
- One mocked tool replay layer.
- One seeded wrong-tool-selection incident.
- One deterministic replay harness.
- One step-level diff / first-divergence report.
- One incident timeline report.
- One CI-style regression gate.

The v1 workflow is an LLM-assisted incident triage pipeline for a synthetic B2B payments API support alert. The seeded incident is a prompt regression that routes a checkout API timeout to the wrong diagnostic tool.

## Hard Non-Goals

Do not build or introduce:

- No dashboard.
- No full tracing backend.
- No enterprise auth.
- No multi-provider live replay.
- No LangSmith/Langfuse clone.
- No vague agent platform.
- No vector database.
- No production deployment.
- No live tool calls during regression replay.
- No multi-incident corpus before the first seeded incident works.

## Technical Defaults

- Use Python.
- Build deterministic components first.
- Use Pydantic models for typed trace, replay, and gate contracts.
- Prefer file-backed artifacts.
- Use cached/synthetic model outputs for v1.
- Use mocked tool responses for v1.
- Keep the trace schema framework-neutral.
- Do not add LangGraph until the custom replay loop works.

## Expected Future Repo Layout

Expected layout once implementation begins:

```text
src/traceforge/
fixtures/
traces/
reports/
docs/
tests/
scripts/
```

Do not create this scaffolding before it is needed.

## Build Discipline

- Prefer small, testable increments.
- Do not implement dashboards or broad platform features.
- Every code change should strengthen the replay loop, trace schema, divergence detection, or gate behavior.
- Do not generate fake "completed" artifacts that are not produced by code.
- Generated reports should be reproducible from traces.

Avoid abstractions that make the project feel like a platform before the first replayable incident works. The first credible artifact is a deterministic incident replay with an accurate first-divergence report and a release gate.

## Verification Expectations

Once implementation begins, include commands and tests with changes. The verification story should prove:

- The gate fails the bad run and passes the patched run.
- The first divergence is Step 1 `requested_tool`.
- Protected fields are explicit.
- Regression replay does not make live tool calls.
- Generated reports are reproducible from trace files.

For the seeded incident, correct behavior selects `service_metrics_lookup` for checkout latency. Bad behavior selects `billing_ledger_lookup`. Downstream differences are expected fallout; the first unacceptable divergence must remain Step 1 `requested_tool`.
