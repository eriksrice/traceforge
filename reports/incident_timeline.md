# Incident Timeline Report

## Incident Summary

The seeded incident is a prompt-regression wrong-tool-selection failure in the checkout API support triage workflow.

## Run Metadata

- Baseline run: `baseline_good`
- Incident run: `incident_bad`
- Baseline events: `12`
- Incident events: `12`

## Timeline

### Baseline
- Step 1 `intake_route` `model_call`: fixture `baseline_good_route`
- Step 1 `intake_route` `state_transition`: transition `route_selected`
- Step 2 `collect_evidence` `tool_call`: tool `service_metrics_lookup` fixture `service_metrics_lookup_checkout_latency`
- Step 2 `collect_evidence` `state_transition`: transition `evidence_collected`
- Step 3 `classify_incident` `model_call`: fixture `baseline_good_classification`
- Step 3 `classify_incident` `state_transition`: transition `incident_classified`

### Incident
- Step 1 `intake_route` `model_call`: fixture `bad_prompt_route`
- Step 1 `intake_route` `state_transition`: transition `route_selected`
- Step 2 `collect_evidence` `tool_call`: tool `billing_ledger_lookup` fixture `billing_ledger_lookup_healthy`
- Step 2 `collect_evidence` `state_transition`: transition `evidence_collected`
- Step 3 `classify_incident` `model_call`: fixture `bad_prompt_classification`
- Step 3 `classify_incident` `state_transition`: transition `incident_classified`

## First Divergence

- Field: `step_1.output.requested_tool`
- Expected: `service_metrics_lookup`
- Observed: `billing_ledger_lookup`
- Root label: `tool_selection_changed`

## Downstream Impact

- `step_1.output.diagnostic_route` changed downstream of `step_1.output.requested_tool`.
- `step_2.tool_name` changed downstream of `step_1.output.requested_tool`.
- `step_2.output.evidence_family` changed downstream of `step_1.output.requested_tool`.
- `step_3.output.incident_type` changed downstream of `step_1.output.requested_tool`.
- `step_3.output.severity` changed downstream of `step_1.output.requested_tool`.
- `step_3.output.engineering_next_action` changed downstream of `step_1.output.requested_tool`.
- `step_3.output.escalation_required` changed downstream of `step_1.output.requested_tool`.

## Patch Status

Patch validation is recorded in `traces/replay_baseline_vs_patched.json` and summarized by the regression gate report.
