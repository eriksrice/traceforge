# First Divergence Report

## Run Pair

- Baseline trace: `trace_checkout_timeout_baseline_good`
- Candidate trace: `trace_checkout_timeout_incident_bad`
- Replay status: `diverged_unacceptable`

## First Unacceptable Divergence

- Field: `step_1.output.requested_tool`
- Expected: `service_metrics_lookup`
- Observed: `billing_ledger_lookup`
- Label: `tool_selection_changed`
- Severity: `blocking`

## Downstream Effects

- `step_1.output.diagnostic_route` changed from `service_health` to `billing_account_review`.
- `step_2.tool_name` changed from `service_metrics_lookup` to `billing_ledger_lookup`.
- `step_2.output.evidence_family` changed from `service_telemetry` to `billing_ledger`.
- `step_3.output.incident_type` changed from `service_regression_after_deploy` to `account_billing_configuration_issue`.
- `step_3.output.severity` changed from `high` to `medium`.
- `step_3.output.engineering_next_action` changed from `Rollback or mitigate checkout-api@2026.06.12 and monitor p95 latency plus 5xx rate.` to `Ask billing operations to review customer account configuration and retry payment records.`.
- `step_3.output.escalation_required` changed from `True` to `False`.

## Reproduction Command

```bash
python -m traceforge replay --baseline traces/baseline_good.jsonl --candidate traces/incident_bad.jsonl
```
