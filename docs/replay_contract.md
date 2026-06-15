# Replay Contract

Replay means reconstructing or re-executing a prior workflow under a declared replay mode and comparing protected behavior fields against a baseline. TraceForge v1 uses cached/synthetic model outputs and mocked tool responses so the replay loop is deterministic before any live provider integrations exist.

## Contract Summary

For deterministic steps, the same incident input hash, prompt fixture, model output fixture, tool fixture, and state transition rules must produce the same protected fields. Any protected-field change is unacceptable unless it is explicitly listed as allowed.

V1 regression replay must not call live models or live tools.

## Replay Modes

- `original`: baseline good behavior using `triage_route_prompt:v1`.
- `incident`: seeded bad behavior using `triage_route_prompt:v2_bad`.
- `patched`: repaired behavior using `triage_route_prompt:v3_patch`.

## Cases And Artifacts

Input fixture:

- `fixtures/incidents/checkout_timeout_input.json`

Planned model output fixtures:

- `fixtures/model_outputs/baseline_good_route.json`
- `fixtures/model_outputs/bad_prompt_route.json`
- `fixtures/model_outputs/patched_prompt_route.json`
- `fixtures/model_outputs/baseline_good_classification.json`
- `fixtures/model_outputs/bad_prompt_classification.json`
- `fixtures/model_outputs/patched_prompt_classification.json`

Planned tool output fixtures:

- `fixtures/tool_outputs/service_metrics_lookup_checkout_latency.json`
- `fixtures/tool_outputs/billing_ledger_lookup_healthy.json`

Planned generated traces:

- `traces/baseline_good.jsonl`
- `traces/incident_bad.jsonl`
- `traces/patched_good.jsonl`

Planned comparison artifacts:

- `traces/replay_baseline_vs_incident.json`
- `traces/replay_baseline_vs_patched.json`

## Step Contract

### Step 1: `intake_route`

Input:

- Synthetic customer escalation from `fixtures/incidents/checkout_timeout_input.json`.

Baseline expected output:

- `requested_tool: service_metrics_lookup`
- `diagnostic_route: service_health`
- `severity_hint: high`

Incident expected output:

- `requested_tool: billing_ledger_lookup`
- `diagnostic_route: billing_account_review`
- `severity_hint: medium`

Patched expected output:

- Protected fields match baseline.

First unacceptable divergence:

- Step 1 field `requested_tool`.

### Step 2: `collect_evidence`

Input:

- Selected tool and normalized incident state from Step 1.

Baseline and patched expected behavior:

- Use mocked `service_metrics_lookup` response.
- Evidence family is `service_telemetry`.
- Evidence includes p95 latency spike, 5xx increase, affected region, correlated timeout errors, and deploy version `checkout-api@2026.06.12`.

Incident expected behavior:

- Use mocked `billing_ledger_lookup` response.
- Evidence family is `billing_ledger`.
- Evidence is plausible but irrelevant: healthy ledger, no disputes, no invoice anomalies, normal account status.

Replay classification:

- Step 2 changes are downstream effects of the Step 1 route divergence unless schema validation fails independently.

### Step 3: `classify_incident`

Input:

- Normalized incident state and evidence bundle from Step 2.

Baseline and patched expected behavior:

- `incident_type: service_regression_after_deploy`
- `severity: high`
- `engineering_next_action`: rollback or mitigation of the checkout API release.
- `escalation_required: true`

Incident expected behavior:

- `incident_type: account_billing_configuration_issue`
- `severity: medium`
- `engineering_next_action`: billing review.
- `escalation_required: false`

Replay classification:

- Step 3 changes are downstream effects of the Step 1 route divergence when Step 1 has already been marked as the root divergence.

## Protected Fields

Blocking protected fields:

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

## Allowed Divergence

Allowed when protected fields match:

- Event ids.
- Timestamps.
- Runtime latency within threshold.
- Tool fixture latency within threshold.
- Cost estimates within threshold.
- Token counts for synthetic fixtures when not used as protected evidence.
- Nonprotected explanatory wording.
- Markdown report formatting.

## Blocking Divergence

Always blocking:

- Wrong tool selected.
- Protected state transition changed.
- Incident type changed.
- Incident severity changed.
- Engineering next action changed materially.
- Escalation requirement changed.
- Schema validation failure.
- Missing required event.
- Replay cannot reproduce the seeded bad run.
- Patched run still follows the bad tool route.
- Live model or live tool call appears in regression replay.
- Volatile field is treated as deterministic release-gating evidence.

## Determinism Classes

- `deterministic`: protected fields are identical across repeated fixture-backed runs.
- `stochastic_stable`: protected fields are stable but nonprotected wording may vary.
- `volatile`: behavior depends on live time, live service state, unpinned model sampling, or unmocked tools.
- `unknown`: insufficient evidence to classify.

V1 expected classifications:

- Step 1 cached model output: `deterministic`.
- Step 2 mocked tool output: `deterministic`.
- Step 3 cached model output: `deterministic`.
- Any live model or tool variant: `volatile` unless moved out of regression-gate evidence.

## Gate Rules

The gate fails when:

- Baseline trace fails schema validation.
- Bad incident cannot be reproduced.
- Bad run does not fail for the expected reason.
- First divergence is not Step 1 `requested_tool`.
- Patched run diverges from baseline on protected fields.
- Live model or tool calls occur during regression replay.
- Required reports cannot be regenerated from trace artifacts.

The gate passes only when:

- Baseline run validates.
- Incident run reproduces the seeded bad behavior.
- Replay reports Step 1 `requested_tool` as first unacceptable divergence.
- Patched run matches baseline protected fields.
- Volatile fields are excluded from release-gating evidence.
- Incident and regression reports are generated from traces.

## Phase 2 Implementation Notes

The first code implementation should encode this contract as typed models and constants before workflow execution is added. Do not implement broad provider adapters, dashboards, or framework abstractions.
