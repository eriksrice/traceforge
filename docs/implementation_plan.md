# TraceForge v1 Implementation Plan

## 1. Build Thesis

TraceForge proves that LLM/tool pipeline incidents can be captured as typed traces, replayed deterministically, diffed at the first divergent step, and converted into CI-style regression gates.

The v1 build should make one realistic wrong-tool-selection incident reproducible. The senior signal is not a broad agent platform; it is a precise reliability artifact that shows trace instrumentation, replay contracts, mocked tool behavior, first-divergence classification, incident reconstruction, and release gating.

## 2. Repo Structure

Future repo tree:

```text
src/traceforge/
fixtures/
traces/
reports/
docs/
tests/
scripts/
```

- `src/traceforge/`: Python package for the trace models, deterministic workflow, replay harness, diff classifier, report generation, gate logic, and command entry points.
- `fixtures/`: Versioned synthetic inputs, cached model outputs, and mocked tool responses used to reproduce the baseline, bad incident, and patched runs without live calls.
- `traces/`: Append-only JSONL trace artifacts emitted by actual TraceForge commands. These files should be generated, not hand-written as completed evidence.
- `reports/`: Generated markdown or JSON reports derived from trace artifacts, including first-divergence, incident timeline, and regression gate reports.
- `docs/`: Design documents, contracts, case-study materials, and implementation notes that can be written before code exists.
- `tests/`: Unit and integration tests for schemas, hashing, fixture loading, workflow traces, replay, diff classification, report generation, and gate behavior.
- `scripts/`: Thin automation wrappers for repeatable demo or local verification commands, only after the underlying package commands exist.

## 3. Core Python Modules

Planned modules and responsibilities:

- `models.py` - typed trace, event, replay, divergence, and gate models. Use Pydantic for explicit contracts and validation.
- `hashing.py` - stable hashing utilities for inputs, outputs, prompts, tool payloads, state snapshots, and event identity inputs.
- `fixtures.py` - load cached model fixtures, mocked tool fixtures, and incident inputs by case, prompt version, tool name, fixture version, and replay mode.
- `workflow.py` - the 3-step incident triage workflow: intake route, evidence collection, and incident classification.
- `tracing.py` - trace capture middleware and append-only event writer for run-scoped JSONL traces.
- `replay.py` - deterministic replay harness that compares baseline, incident, and patched runs under declared replay modes.
- `diff.py` - first-divergence comparator that distinguishes root divergence from downstream fallout.
- `reports.py` - incident timeline and regression report generators that read trace and comparison artifacts.
- `gate.py` - CI-style pass/fail gate that validates schema, replay reproduction, protected-field comparison, volatility rules, and report generation.
- `cli.py` - command entry points for run, replay, report, and gate commands.

Prefer deterministic Python components over unnecessary agents. Do not add LangGraph or provider integrations until the custom replay loop works.

## 4. Fixture Plan

Planned fixture files:

- `fixtures/incidents/checkout_timeout_input.json`: the synthetic customer escalation input. Expected contents: customer escalation text, customer id, affected checkout API service, incident time window, release context, and expected case id.
- `fixtures/model_outputs/baseline_good_route.json`: cached Step 1 model output for `triage_route_prompt:v1`. Expected contents: normalized intake fields, `diagnostic_route`, `requested_tool: service_metrics_lookup`, prompt/model metadata, and output hash inputs.
- `fixtures/model_outputs/bad_prompt_route.json`: cached Step 1 model output for `triage_route_prompt:v2_bad`. Expected contents: the same normalized input shape but `requested_tool: billing_ledger_lookup`, plus metadata showing the bad prompt version.
- `fixtures/model_outputs/patched_prompt_route.json`: cached Step 1 model output for `triage_route_prompt:v3_patch`. Expected contents: restored `requested_tool: service_metrics_lookup` behavior and patch prompt metadata.
- `fixtures/model_outputs/baseline_good_classification.json`: cached Step 3 model output for the good path. Expected contents: `incident_type: service_regression_after_deploy`, `severity: high`, telemetry-based evidence, rollback or mitigation next action, and `escalation_required: true`.
- `fixtures/model_outputs/bad_prompt_classification.json`: cached Step 3 model output for the bad path. Expected contents: `incident_type: account_billing_configuration_issue`, `severity: medium`, billing-review recommendation, and `escalation_required: false`.
- `fixtures/model_outputs/patched_prompt_classification.json`: cached Step 3 model output for the patched path. Expected contents: protected fields matching the baseline good classification.
- `fixtures/tool_outputs/service_metrics_lookup_checkout_latency.json`: mocked tool response for the correct diagnostic route. Expected contents: checkout API p95 latency spike, 5xx increase, affected region, deploy version `checkout-api@2026.06.12`, correlated timeout errors, status labels, timestamps, realistic latency, and fixture version.
- `fixtures/tool_outputs/billing_ledger_lookup_healthy.json`: mocked tool response for the wrong but plausible diagnostic route. Expected contents: healthy ledger status, no payment disputes, no invoice anomalies, normal account status, status labels, timestamps, realistic latency, and fixture version.

Fixtures should be credible enough that the wrong run fails operationally without failing syntactically.

## 5. Trace Artifact Plan

Expected generated trace and comparison files:

- `traces/baseline_good.jsonl`: proves the good 3-step workflow can emit valid append-only trace events with `service_metrics_lookup` and high-severity service regression classification.
- `traces/incident_bad.jsonl`: proves the seeded bad prompt regression can be reproduced with `billing_ledger_lookup` and a plausible but wrong billing classification.
- `traces/patched_good.jsonl`: proves the patched prompt restores baseline protected behavior while still using deterministic fixtures.
- `traces/replay_baseline_vs_incident.json`: proves the replay comparator identifies the first unacceptable divergence at Step 1 `requested_tool` and labels later changes as downstream effects.
- `traces/replay_baseline_vs_patched.json`: proves protected fields in the patched run match the baseline or are explicitly allowed.
- `traces/regression_gate_result.json`: proves the gate fails the bad run for the expected reason and passes the patched run.

Trace artifacts must be emitted by commands, not manually written as fake completed outputs.

## 6. Report Artifact Plan

Generated reports form one bounded evidence packet, not a dashboard or broad reporting surface:

- `reports/first_divergence_report.md`
  - Required sections: run pair, comparison inputs, protected fields, first unacceptable divergence, expected value, observed value, divergence label, severity, downstream effects, allowed-field summary, and reproduction command.
- `reports/incident_timeline.md`
  - Required sections: incident summary, run metadata, prompt/model/tool versions, step-by-step timeline, first divergence, evidence collected, downstream classification impact, patch status, gate status, and human-review note.
- `reports/regression_gate_report.md`
  - Required sections: gate name, gate status, checked traces, schema validation result, bad-run reproduction result, first-divergence result, patched-run protected-field result, volatility checks, generated artifact list, and release recommendation.
- `docs/architecture_brief.md`
  - Required sections: problem, v1 workflow, trace event schema summary, replay contract, mocked tool design, divergence classifier design, gate rules, non-goals, and future extension points.

Reports must be reproducible from trace and comparison artifacts.

## 7. CLI / Command Plan

Implemented reviewer-facing commands:

```bash
python -m traceforge run --case baseline
python -m traceforge run --case incident
python -m traceforge run --case patched
python -m traceforge replay --baseline traces/baseline_good.jsonl --candidate traces/incident_bad.jsonl
python -m traceforge replay --baseline traces/baseline_good.jsonl --candidate traces/patched_good.jsonl
python -m traceforge report first-divergence --comparison traces/replay_baseline_vs_incident.json
python -m traceforge report timeline --baseline traces/baseline_good.jsonl --trace traces/incident_bad.jsonl --comparison traces/replay_baseline_vs_incident.json
python -m traceforge gate
```

The report commands intentionally regenerate the first-divergence and incident-timeline markdown from existing trace and comparison artifacts. `traceforge gate` remains the canonical one-command reviewer path because it regenerates traces, comparisons, reports, and the gate result together.

## 8. Acceptance Tests

Tests that must eventually pass:

- Trace schema validation rejects missing required fields and invalid enum values.
- Baseline trace generation emits all three workflow steps in order.
- Bad incident reproduction selects `billing_ledger_lookup` and produces the wrong but plausible classification.
- First-divergence detection reports Step 1 `requested_tool`.
- Downstream divergence classification marks tool response, evidence bundle, incident type, severity, and action changes as fallout from the Step 1 route change.
- Patched run passes protected-field comparison against baseline.
- Gate fails the bad run.
- Gate passes the patched run.
- Volatile/live fields are not treated as deterministic evidence.
- Replay never makes live tool calls during regression mode.
- Generated reports can be reproduced from trace and comparison artifacts.

## 9. Protected Fields

Protected fields for comparison:

- `requested_tool`
- `incident_type`
- `severity`
- `engineering_next_action`
- `escalation_required`
- Key state transition labels, including diagnostic route, evidence family, and classification path.
- Trace schema validity.

Allowed to vary when explicitly marked:

- Event ids.
- Timestamps.
- Runtime latency within threshold.
- Cost estimates within threshold.
- Nonprotected explanatory wording when protected fields match.
- Report prose formatting when the underlying trace-derived facts match.

Unacceptable divergence includes wrong tool selection, changed protected state transition, changed severity, changed root-cause class, schema validation failure, missing required event, inability to reproduce the bad run, or a patched run that still follows the bad tool route.

## 10. Build Phases

### Phase 1: Define The Contract

- Objective: Convert the design into concrete schemas, protected fields, replay rules, and fixture contracts.
- Files to create later: `docs/trace_schema.md`, `docs/replay_contract.md`, `docs/evaluation_plan.md`, `fixtures/incidents/checkout_timeout_input.json`.
- Acceptance criteria: 3-step workflow is frozen, required trace fields are documented, protected fields are explicit, baseline/bad/patched fixture paths are specified.
- Estimated complexity: Medium.
- Risks: Overdesigning the schema before replay exists; leaving protected fields vague.
- Stopping point: The next implementation session can scaffold models and fixtures without making new design decisions.

### Phase 2: Scaffold Minimal Package And Models

- Objective: Create the smallest Python package structure and Pydantic contracts needed for trace events, replay comparisons, divergence labels, and gate results.
- Files to create later: `src/traceforge/__init__.py`, `src/traceforge/models.py`, `src/traceforge/hashing.py`, `tests/test_models.py`, `tests/test_hashing.py`.
- Acceptance criteria: Models validate required fields, enums cover replay and divergence states, hashing is stable across repeated runs.
- Estimated complexity: Medium.
- Risks: Building a general tracing SDK instead of the v1 schema.
- Stopping point: Schema and hashing tests pass locally.

### Phase 3: Add Fixtures And Fixture Loading

- Objective: Add deterministic incident input, cached model outputs, and mocked tool outputs for baseline, bad, and patched paths.
- Files to create later: files under `fixtures/incidents/`, `fixtures/model_outputs/`, `fixtures/tool_outputs/`, `src/traceforge/fixtures.py`, `tests/test_fixtures.py`.
- Acceptance criteria: Fixture loader resolves each case deterministically, validates shape, and rejects missing versions.
- Estimated complexity: Low to medium.
- Risks: Mocked data feels too thin or obviously staged.
- Stopping point: All required fixtures load through typed interfaces.

### Phase 4: Capture Baseline And Incident Traces

- Objective: Implement the custom 3-step workflow and append-only event writer for baseline and bad runs.
- Files to create later: `src/traceforge/workflow.py`, `src/traceforge/tracing.py`, `src/traceforge/cli.py`, generated traces under `traces/`, and workflow/tracing tests.
- Acceptance criteria: Good run emits valid events for all 3 steps; bad run emits valid events with `billing_ledger_lookup`; event order reconstructs the workflow.
- Estimated complexity: Medium to high.
- Risks: Capturing logs instead of replayable typed state; accidentally creating live-call paths.
- Stopping point: Baseline and incident traces are generated by commands and validate against the schema.

### Phase 5: Build Replay And First-Divergence Diff

- Objective: Compare baseline and incident traces, detect first unacceptable divergence, and classify downstream effects.
- Files to create later: `src/traceforge/replay.py`, `src/traceforge/diff.py`, replay comparison artifacts under `traces/`, and replay/diff tests.
- Acceptance criteria: Comparator reports Step 1 `requested_tool` as first divergence, labels later changes as downstream, and ignores allowed volatile fields.
- Estimated complexity: High.
- Risks: Producing a shallow JSON diff rather than causal first-divergence analysis.
- Stopping point: Baseline-vs-incident comparison fails exactly where expected.

### Phase 6: Patch, Gate, And Reports

- Objective: Add patched fixture path, generate trace-derived reports, and enforce CI-style pass/fail gate behavior.
- Files to create later: `src/traceforge/reports.py`, `src/traceforge/gate.py`, generated reports under `reports/`, gate artifacts under `traces/`, and report/gate tests.
- Acceptance criteria: Bad run fails the gate; patched run passes; reports are regenerated from trace artifacts; no live tool calls occur during regression replay.
- Estimated complexity: High.
- Risks: Gate checks become too weak; reports describe a failure without proving replay.
- Stopping point: `python -m traceforge gate` gives a reviewer a clear pass/fail result with supporting artifacts.

### Phase 7: Public Case Study Polish

- Objective: Add README case study and demo script after the implementation is real and reproducible.
- Files to create later: `README.md`, `scripts/demo.sh`, optional `docs/failure_modes.md`.
- Acceptance criteria: README explains the incident and commands; demo script runs the generated artifact path; claims match actual tests and traces.
- Estimated complexity: Low to medium.
- Risks: Marketing copy outruns the implementation.
- Stopping point: A senior reviewer can clone, run, inspect, and understand the project.

### Phase 7.5: Alignment Patch

- Objective: Close the literal gap between the planned report CLI and the implemented v1 surface while preserving the red-team constraint against broad reporting scope.
- Files created or updated: `src/traceforge/cli.py`, `tests/test_cli.py`, `README.md`, and `docs/implementation_plan.md`.
- Acceptance criteria: `traceforge report first-divergence` and `traceforge report timeline` regenerate markdown from existing artifacts; docs describe reports as one bounded evidence packet; tests cover the report commands.
- Estimated complexity: Low.
- Risks: Report commands could become a second workflow runner instead of a thin artifact regeneration surface.
- Stopping point: CLI, tests, README, and plan all agree on the v1 report behavior.

## 11. Senior Reviewer Proof Checklist

A Staff Engineer or senior AI platform reviewer should be able to inspect:

- Typed event schema.
- Append-only trace.
- Realistic mocked tool output.
- First-divergence classifier.
- Incident timeline.
- CI-style gate.
- Reproducible commands.
- Tests.
- README case study.

The review should answer: what changed first, why it mattered, whether the fix worked, and why the release gate is trustworthy.

## 12. Anti-Scope-Creep Guardrails

Hard non-goals:

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
- No full observability platform.
- No distributed tracing service.
- No large benchmark suite.
- No real customer data.
- No root-cause hypothesis agent in v1.
- No broad framework abstraction before the custom replay loop works.

Deferred scope only after v1 works: LangGraph adapter, live-provider replay mode, multiple workflow topologies, human review queue, richer determinism statistics, browser/dashboard view, and external CI provider integration.

## 13. README / Case Study Outline

Future README structure:

- Problem.
- Why LLM incidents are hard to reproduce.
- TraceForge concept.
- Architecture.
- Demo commands.
- Generated artifacts.
- Evaluation strategy.
- Failure modes.
- Limitations.
- Future work.

README claims must point to real code, tests, traces, and generated reports. Do not describe artifacts as completed until commands produce them.

## 14. Implementation Readiness Verdict

READY FOR REPO SCAFFOLD

Exact next Codex task:

Create the minimal Python project scaffold for TraceForge v1 with `src/traceforge/`, `tests/`, and initial typed models for trace events, replay comparisons, divergence labels, protected fields, and gate results. Include only the schema/hashing unit tests needed for Phase 2. Do not generate traces or reports until the workflow and fixture loader exist.
