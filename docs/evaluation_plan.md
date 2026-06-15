# Evaluation Plan

TraceForge v1 evaluation proves a narrow replay loop, not a broad benchmark. The project succeeds when one realistic wrong-tool-selection incident is captured, replayed, diffed at the first divergent step, patched, and enforced by a CI-style gate.

## Evaluation Thesis

The seeded bad run should look operationally plausible while still being wrong. The evaluator must show that TraceForge can identify the first causal divergence rather than merely diffing the final incident response.

## Fixture-Backed Cases

### Baseline Good Case

- Input fixture: `fixtures/incidents/checkout_timeout_input.json`.
- Prompt version: `triage_route_prompt:v1`.
- Step 1 route fixture: `fixtures/model_outputs/baseline_good_route.json`.
- Tool fixture: `fixtures/tool_outputs/service_metrics_lookup_checkout_latency.json`.
- Step 3 classification fixture: `fixtures/model_outputs/baseline_good_classification.json`.
- Expected trace: `traces/baseline_good.jsonl`.
- Expected result: high-severity service regression after deploy.

### Incident Bad Case

- Input fixture: `fixtures/incidents/checkout_timeout_input.json`.
- Prompt version: `triage_route_prompt:v2_bad`.
- Step 1 route fixture: `fixtures/model_outputs/bad_prompt_route.json`.
- Tool fixture: `fixtures/tool_outputs/billing_ledger_lookup_healthy.json`.
- Step 3 classification fixture: `fixtures/model_outputs/bad_prompt_classification.json`.
- Expected trace: `traces/incident_bad.jsonl`.
- Expected result: plausible but wrong billing configuration classification.

### Patched Good Case

- Input fixture: `fixtures/incidents/checkout_timeout_input.json`.
- Prompt version: `triage_route_prompt:v3_patch`.
- Step 1 route fixture: `fixtures/model_outputs/patched_prompt_route.json`.
- Tool fixture: `fixtures/tool_outputs/service_metrics_lookup_checkout_latency.json`.
- Step 3 classification fixture: `fixtures/model_outputs/patched_prompt_classification.json`.
- Expected trace: `traces/patched_good.jsonl`.
- Expected result: protected fields match baseline.

## Required Checks

- Trace schema validation rejects missing required fields and invalid enum values.
- Baseline trace generation emits all three workflow steps in order.
- Bad incident reproduction selects `billing_ledger_lookup`.
- Bad incident reproduction produces `account_billing_configuration_issue`.
- First-divergence detection reports Step 1 `requested_tool`.
- Downstream divergence classification marks tool response, evidence bundle, incident type, severity, and action changes as fallout from the Step 1 route change.
- Patched run selects `service_metrics_lookup`.
- Patched run classifies `service_regression_after_deploy`.
- Patched run sets severity `high`.
- Patched run sets `escalation_required: true`.
- Patched run passes protected-field comparison against baseline.
- Gate fails the bad run.
- Gate passes the patched run.
- Volatile/live fields are not treated as deterministic evidence.
- Regression replay never makes live tool calls.
- Generated reports can be reproduced from trace and comparison artifacts.

## First-Divergence Assertion

The canonical first-divergence assertion is:

- Step: `1`
- Step name: `intake_route`
- Field path: `step_1.output.requested_tool`
- Baseline value: `service_metrics_lookup`
- Incident value: `billing_ledger_lookup`
- Divergence label: `tool_selection_changed`
- Severity: `blocking`

Step 2 and Step 3 differences are expected downstream effects unless they reveal an independent schema error or missing event.

## Protected-Field Assertions

Baseline and patched must match on:

- `requested_tool`
- `diagnostic_route`
- `tool_name`
- `evidence_family`
- `incident_type`
- `severity`
- `engineering_next_action`
- `escalation_required`
- Key state transition labels.
- Trace schema validity.

The bad incident must differ on `requested_tool` and may differ downstream on tool response, evidence family, incident type, severity, engineering action, and escalation flag.

## Determinism Score

Use a simple score per step:

- `1.0`: protected fields are identical across replays.
- `0.5`: protected fields are stable but nonprotected text varies.
- `0.0`: protected fields vary, required fields are missing, or replay uses live unpinned services.

Expected v1 scores:

- Step 1 cached output: `1.0`.
- Step 2 mocked tool output: `1.0`.
- Step 3 cached output: `1.0`.
- Any live model/tool path used for regression replay: `0.0`.

## Gate Acceptance Criteria

The v1 gate passes only when:

- `traces/baseline_good.jsonl` validates.
- `traces/incident_bad.jsonl` validates.
- `traces/patched_good.jsonl` validates.
- Baseline versus incident replay finds Step 1 `requested_tool` as first divergence.
- Baseline versus patched replay has no blocking protected-field divergence.
- Incident timeline and regression gate reports are generated from trace artifacts.
- Regression replay uses no live tool or model calls.

The v1 gate fails when:

- Any required trace is missing or invalid.
- The bad run cannot be reproduced.
- The bad run passes.
- The first divergence is missing or not Step 1 `requested_tool`.
- The patched run still selects `billing_ledger_lookup`.
- The patched run changes incident type, severity, engineering action, or escalation flag relative to baseline.
- Volatile steps are counted as deterministic evidence.

## Phase 1 Stopping Point

Phase 1 is complete when:

- The trace schema contract is concrete enough to become Pydantic models.
- The replay contract names modes, artifacts, protected fields, and blocking rules.
- This evaluation plan names the fixture-backed cases and acceptance checks.
- The first incident input fixture exists and does not claim any generated trace or report already exists.
