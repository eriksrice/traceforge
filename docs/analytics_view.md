# TraceForge Analytics View

TraceForge traces are operational artifacts, but they are also an analytical dataset. This view explains how a reviewer can inspect the replay system through an AI Analytics Engineer lens.

## Event Grain

One row in a trace file represents one typed workflow event:

- `step_start`
- `model_call`
- `tool_call`
- `state_transition`
- `step_end`
- `replay_comparison`
- `gate_result`

The natural grain is:

```text
trace_id + run_id + event_id
```

## Core Dimensions

- `case_id`: baseline, incident, or patched run.
- `incident_id`: seeded incident identifier.
- `workflow_name`: workflow under replay.
- `step_index`: workflow step number.
- `step_name`: semantic step label.
- `event_type`: event contract variant.
- `model_fixture_id`: cached model output source.
- `tool_name`: mocked tool contract selected.
- `tool_fixture_id`: mocked tool response source.
- `determinism_class`: deterministic, volatile, or ignored evidence category.

## Core Measures

- Event count by run.
- Protected-field match rate.
- First-divergence step index.
- Blocking divergence count.
- Downstream divergence count.
- Gate pass/fail status.
- Report regeneration status.

## Protected Fields As Business-Critical Metrics

Protected fields are the release-gate evidence set:

- `step_1.output.requested_tool`
- `step_1.output.diagnostic_route`
- `step_1.state.transition_label`
- `step_2.tool_name`
- `step_2.output.evidence_family`
- `step_2.state.transition_label`
- `step_3.output.incident_type`
- `step_3.output.severity`
- `step_3.output.engineering_next_action`
- `step_3.output.escalation_required`
- `step_3.state.transition_label`
- `trace.schema_valid`

These fields turn a replay into a deterministic comparison: bad runs should fail when protected behavior changes, and patched runs should pass when protected behavior returns to baseline.

## Example Analytical Questions

- Which step first changed protected behavior?
- Did the tool call change before the final classification changed?
- Which downstream state transitions were effects of the root divergence?
- Did the patched run restore the protected-field contract?
- Would this release be blocked by CI?

## Why This Matters

The same trace contract can support debugging, evaluation, and release analytics. TraceForge v1 keeps the storage layer simple, but the event shape is intentionally compatible with later warehouse, notebook, or BI analysis.
