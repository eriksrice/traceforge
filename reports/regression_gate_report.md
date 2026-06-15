# Regression Gate Report

## Gate Result

- Gate: `traceforge-seeded-regression`
- Status: `pass`
- Incident: `checkout_timeout_wrong_tool`
- Review required: `False`

## Checks

- Bad run status: `diverged_unacceptable`
- Bad run first divergence: `step_1.output.requested_tool`
- Patched run status: `matched`
- Patched first divergence: `None`

## Checked Traces

- `traces/baseline_good.jsonl`
- `traces/incident_bad.jsonl`
- `traces/patched_good.jsonl`
- `traces/replay_baseline_vs_incident.json`
- `traces/replay_baseline_vs_patched.json`

## Generated Reports

- `reports/first_divergence_report.md`
- `reports/incident_timeline.md`
- `reports/regression_gate_report.md`

## Blocking Reasons

- None.
