# TraceForge Project Architect Handoff

## 1. Project One-Liner

TraceForge is a file-backed incident replay system for LLM/tool pipelines that captures typed traces, deterministically replays an incident, identifies the first divergent step, and turns the fixed trace into a CI-style regression gate.

## 2. Senior Hiring Signal

TraceForge should signal production AI reliability work, not another agent demo. The project proves Erik can reason about trace instrumentation, event schemas, deterministic replay, mocked tool contracts, divergence classification, incident reconstruction, and release gating for LLM systems.

The key senior signal is that failure is treated as an operational artifact. A bad run is not just logged; it is captured as a replayable event bundle, compared against a known-good baseline, explained at the step level, and converted into a regression test that blocks future releases.

## 3. Enterprise Analogue

Enterprise AI platform teams need to investigate LLM incidents after prompts, tools, model versions, and intermediate states have changed. Conventional logs often cannot answer:

- Which step first changed?
- Was the change caused by prompt behavior, model output, tool response, state transition, retry logic, or nondeterminism?
- Can the original incident be reproduced without hitting live services?
- Does the proposed fix actually prevent the same failure class from shipping again?

TraceForge is the small local analogue of incident replay infrastructure for AI applications.

## 4. Core User / Buyer

Primary user: AI platform engineer, LLM systems engineer, or MLOps engineer responsible for production LLM workflow reliability.

Secondary buyer: Engineering leader who needs release confidence for prompt/model/tool changes and wants auditable evidence that incidents can be reproduced, fixed, and regression-tested.

The v1 user is not a business end user. The v1 user is the engineer debugging a failed LLM/tool pipeline and deciding whether a patch is safe to release.

## 5. Concrete V1 Workflow

Use a small custom Python tool-calling pipeline, not LangGraph, for v1. Keep the trace schema framework-neutral so LangGraph can be added later without making the first build depend on framework ceremony.

The workflow is an LLM-assisted incident triage pipeline for a synthetic B2B payments API support alert.

### Step 1: Intake Normalization And Diagnostic Route

Input: A customer escalation saying checkout API requests are timing out after a release.

The LLM step extracts:

- customer_id
- affected_service
- symptom
- time_window
- severity_hint
- diagnostic_route
- requested_tool

Allowed diagnostic tools:

- `service_metrics_lookup`
- `deploy_changelog_lookup`
- `billing_ledger_lookup`
- `runbook_search`

Correct behavior: select `service_metrics_lookup` first for checkout latency, then preserve state indicating that deployment evidence may be needed.

### Step 2: Evidence Collection With Mocked Tools

The pipeline calls the selected tool through TraceForge's mocked tool replay layer.

Correct tool response should include realistic service telemetry:

- checkout API p95 latency spike
- 5xx increase
- affected region
- deployment version in the incident window
- correlated timeout errors

Bad tool response should be realistic but wrong for the incident:

- billing ledger is healthy
- no payment disputes
- no invoice anomalies
- normal account status

### Step 3: Incident Classification And Response Plan

The LLM step produces a typed incident packet:

- incident_type
- suspected_root_cause
- severity
- evidence_used
- customer_safe_summary
- engineering_next_action
- confidence
- escalation_required

Correct behavior: classify as `service_regression_after_deploy`, severity `high`, recommend rollback or mitigation, and cite telemetry/deploy evidence.

Bad behavior: classify as `account_billing_configuration_issue`, severity `medium`, recommend billing review, and miss the production service regression.

## 6. Seeded Incident

Seeded incident type: prompt regression causing wrong tool selection.

Starting condition:

- Baseline prompt version `triage_route_prompt:v1` correctly maps checkout API timeout language to `service_metrics_lookup`.
- Regression prompt version `triage_route_prompt:v2_bad` overweights examples containing the words "billing", "payment", or "checkout" and routes the same support alert to `billing_ledger_lookup`.
- Model outputs are cached/synthetic fixtures in v1 so the replay system can prove mechanics deterministically.

Expected behavior:

- Step 1 selects `service_metrics_lookup`.
- Step 2 retrieves service telemetry showing p95 latency and error-rate regression after deploy `checkout-api@2026.06.12`.
- Step 3 classifies the incident as a service regression and emits a high-severity engineering escalation.

Bad behavior:

- Step 1 selects `billing_ledger_lookup`.
- Step 2 retrieves irrelevant but plausible billing data.
- Step 3 misclassifies the incident as account/billing configuration noise and fails to escalate the production service regression.

Where the divergence occurs:

- First divergence is Step 1, field `requested_tool`.
- Downstream divergences are expected consequences: tool response family, evidence bundle, incident type, severity, and recommended action.

Why this resembles a real production LLM incident:

- Prompt examples often bias tool routing unexpectedly.
- A wrong but syntactically valid tool call can produce plausible evidence.
- The final answer can look confident while being operationally wrong.
- Conventional output diffs may catch the final answer change but miss the first causal step.
- Safe reproduction requires mocking tool responses rather than re-querying live systems.

## 7. V1 Architecture

TraceForge v1 should be deterministic Python components with typed boundaries and file artifacts.

### Trace Capture Middleware

Wrap each workflow step with a trace emitter that records inputs, outputs, model configuration, prompt version, tool calls, state transitions, hashes, latency, replay mode, and errors. The middleware should be explicit and boring: function wrapper in v1, not a generalized SDK.

### Append-Only Event Store

Write newline-delimited JSON events to a run-scoped trace file. Events are append-only. Derived reports can be regenerated from the event file.

Likely later artifact:

- `traces/{run_id}.jsonl`
- `traces/{run_id}.manifest.json`

### Replay Harness

Load a prior trace bundle and replay the same step sequence under a selected config:

- original config
- bad prompt config
- patched prompt config

The harness should compare baseline, incident, and patched runs at the step and field level.

### Mocked Tool Response Layer

Use typed fixtures keyed by:

- tool_name
- input_hash
- fixture_version
- replay_mode

Mock responses should be realistic enough to show that the wrong tool did not fail noisily; it returned plausible but irrelevant evidence.

### Divergence Classifier

Compare expected and observed events. Classify divergences as:

- `none`
- `allowed_nondeterministic`
- `prompt_output_changed`
- `tool_selection_changed`
- `tool_response_changed`
- `state_transition_changed`
- `schema_violation`
- `missing_event`
- `unexpected_error`

The classifier should identify the first unacceptable divergence and distinguish root divergence from downstream fallout.

### Incident Timeline Generator

Generate a markdown or JSON report that reconstructs the incident in order:

- run metadata
- prompt/model/tool versions
- trace steps
- first divergence
- downstream impacts
- replay status
- patch status
- release-gate result

### CI Regression Gate

A command later should run the seeded regression suite and exit nonzero when:

- the bad run is not reproduced
- the first divergence is not detected
- a patched run still diverges on protected fields
- volatile steps are treated as deterministic without being pinned or mocked
- required trace fields are missing

## 8. Trace Event Schema

Use typed events. Pydantic models are appropriate later, but this handoff only defines fields.

Core event fields:

- `event_id`: stable unique event id
- `trace_id`: workflow trace id
- `run_id`: execution run id
- `parent_event_id`: parent event when applicable
- `step_index`: integer step order
- `step_name`: e.g. `intake_route`, `collect_evidence`, `classify_incident`
- `event_type`: `step_start`, `model_call`, `tool_call`, `state_transition`, `step_end`, `replay_comparison`, `gate_result`
- `timestamp_start`: ISO-8601 UTC
- `timestamp_end`: ISO-8601 UTC
- `latency_ms`: measured duration
- `status`: `started`, `success`, `error`, `skipped`, `replayed`

Model and prompt fields:

- `model_provider`: e.g. `synthetic`, `openai`, `anthropic`
- `model_name`
- `model_version`
- `temperature`
- `seed`
- `prompt_id`
- `prompt_version`
- `prompt_hash`
- `system_prompt_hash`
- `input_hash`
- `output_hash`
- `token_input_count`
- `token_output_count`
- `estimated_cost_usd`
- `model_output_mode`: `cached`, `synthetic`, `live`

Tool-call fields:

- `tool_name`
- `tool_version`
- `tool_call_id`
- `tool_input`
- `tool_input_hash`
- `tool_output`
- `tool_output_hash`
- `tool_latency_ms`
- `tool_status`
- `tool_error_type`
- `tool_fixture_id`
- `tool_fixture_version`
- `tool_replay_mode`: `mocked`, `live`, `skipped`

State transition fields:

- `state_before_hash`
- `state_after_hash`
- `state_patch`
- `state_schema_version`
- `transition_label`
- `protected_fields`
- `changed_fields`

Replay and divergence fields:

- `baseline_event_id`
- `replay_event_id`
- `replay_mode`: `original`, `incident`, `patched`
- `replay_status`: `matched`, `diverged_allowed`, `diverged_unacceptable`, `not_replayable`
- `determinism_class`: `deterministic`, `stochastic_stable`, `volatile`, `unknown`
- `divergence_label`
- `divergence_severity`: `none`, `info`, `warning`, `blocking`
- `first_divergence`: boolean
- `root_divergence_event_id`
- `allowed_divergence_reason`

Governance fields:

- `incident_id`
- `decision_record_id`
- `release_candidate_id`
- `gate_name`
- `gate_status`: `pass`, `fail`, `warn`
- `review_required`: boolean
- `notes`

## 9. Replay Contract

Replay means re-executing or reconstructing a prior workflow trace under a declared replay mode and comparing protected behavior fields against a baseline.

### Deterministic Replay

For deterministic steps, the same input hash, prompt hash, model output fixture, tool fixture, and state transition should produce the same protected output fields. Any protected field change is unacceptable unless explicitly labeled as allowed.

### Cached/Synthetic Model Output Replay

V1 should use cached/synthetic model outputs, not live provider calls. The point is to prove replay mechanics, trace schema, divergence detection, and gate behavior. Live provider calls can be deferred because they would add nondeterminism before the replay contract is proven.

Model output fixtures should represent:

- baseline good route
- bad prompt route
- patched good route

### Mocked Tool Replay

Tool replay should use fixtures that mimic production tool responses. The fixture must preserve:

- response shape
- status codes or status labels
- realistic latency
- plausible partial data
- timestamps
- fixture version
- error or timeout metadata when used

Mocking is not a shortcut around credibility. The mocked billing response must be plausible enough that the bad workflow can fail in a realistic way.

### Volatile Step Handling

Any step that depends on live time, live external services, unconstrained LLM sampling, or unpinned tools must be labeled volatile unless pinned or mocked. Volatile steps can appear in traces, but they cannot be used as release-blocking regression evidence until stabilized.

### Allowed Vs. Unacceptable Divergence

Allowed divergence:

- event ids
- timestamps
- runtime latency within threshold
- cost estimates within threshold
- nonprotected explanatory wording when protected fields match

Unacceptable divergence:

- wrong tool selected
- protected state transition changed
- incident severity changed
- root-cause class changed
- schema validation failure
- missing required event
- replay cannot reproduce the seeded bad run
- patched run still follows the bad tool route

## 10. Evaluation Strategy

### Replay Reproduction Tests

The seeded bad trace must replay to the same first divergence and same bad final classification under `triage_route_prompt:v2_bad`.

### First-Divergence Detection

The comparator must report Step 1 `requested_tool` as the first unacceptable divergence. It should mark Step 2 and Step 3 as downstream effects, not separate root causes.

### Determinism Scoring

Run each fixture-backed step multiple times and classify:

- Step 1 with cached outputs: deterministic
- Step 2 with mocked tool fixtures: deterministic
- Step 3 with cached outputs: deterministic
- Any live model/tool variant: volatile unless pinned and measured stable

Scoring can be simple in v1:

- `1.0`: protected fields identical across replays
- `0.5`: protected fields stable but unprotected text varies
- `0.0`: protected fields vary or required fields missing

### Seeded Regression Suite

Include three trace cases later:

- good baseline case
- bad prompt regression case
- patched prompt case

V1 should not add a broad benchmark set. One vivid incident plus a tiny regression suite is enough.

### Patched Replay Comparison

The patched prompt version must:

- select `service_metrics_lookup`
- retrieve telemetry evidence
- classify `service_regression_after_deploy`
- set severity `high`
- pass protected-field comparison against the known-good baseline

### Release-Gate Pass/Fail Rules

Gate fails when:

- trace schema validation fails
- seeded incident cannot be reproduced
- first divergence is not identified
- bad run passes
- patched run fails protected-field comparison
- volatile steps are included as deterministic evidence

Gate passes only when:

- baseline run validates
- bad run fails for the expected reason
- patched run passes
- incident report and regression report are generated from trace artifacts

## 11. Observability / Governance Angle

TraceForge treats traces as auditable event bundles. Each bundle records versions, inputs, outputs, tool calls, state transitions, costs, latency, replay mode, and divergence labels. This supports operational governance because a release decision can point to concrete trace evidence rather than informal debugging notes.

Incident decision records should summarize:

- what failed
- where it first diverged
- which version introduced the failure
- which fields were protected
- which patch was tested
- why the release gate passed or failed
- whether human review is required

The governance story is not compliance theater. It is simple engineering accountability: every release gate result should be reproducible from saved trace events.

## 12. Failure Modes

### System Failure Modes

- Trace events miss a required field, making replay ambiguous.
- Input/output hashes are inconsistent or computed after mutation.
- Mocked tools return unrealistic data and make the incident feel staged.
- Replay accidentally calls live tools and changes evidence.
- Comparator over-focuses on final output and misses first divergence.
- Comparator flags harmless wording changes as release-blocking.
- Volatile steps are treated as deterministic.
- State transition metadata is too thin to explain downstream effects.
- Regression gate passes because protected fields are poorly chosen.

### Portfolio Failure Modes

- Looking like simple log capture.
- Relying on unrealistic mocks.
- Becoming too abstract.
- Dashboard/platform scope creep.
- Weak or boring seeded incident.
- Framing it as a vague agent platform.
- Over-indexing on LangGraph before replay mechanics work.
- Adding broad provider integrations before the core incident loop is credible.
- Producing reports that describe the failure but do not prove reproduction.

## 13. MVP Build Phases

### Phase 1: Define The Contract

Goal: Turn this handoff into concrete schemas, fixtures, and protected fields.

Files/artifacts likely created later:

- `docs/trace_schema.md`
- `docs/replay_contract.md`
- `docs/evaluation_plan.md`
- `fixtures/incidents/checkout_timeout_wrong_tool.yaml`

Acceptance criteria:

- The 3-step workflow is frozen.
- Required trace fields are documented.
- Protected fields are explicit.
- Baseline, bad, and patched fixture paths are specified.

Risk:

- Overdesigning schemas before the replay path exists.

### Phase 2: Capture A Baseline Trace

Goal: Build the minimum workflow wrapper that emits append-only trace events for the good run.

Files/artifacts likely created later:

- `src/traceforge/workflow.py`
- `src/traceforge/tracing.py`
- `traces/baseline_good.jsonl`

Acceptance criteria:

- Good run emits valid events for all 3 steps.
- Model/prompt/tool/state hashes are present.
- Event order reconstructs the workflow.

Risk:

- Capturing logs rather than typed replayable state.

### Phase 3: Seed And Reproduce The Incident

Goal: Add the bad prompt fixture and replay it against the same input.

Files/artifacts likely created later:

- `fixtures/model_outputs/bad_prompt_route.json`
- `fixtures/tool_outputs/billing_ledger_healthy.json`
- `traces/incident_bad.jsonl`

Acceptance criteria:

- Bad run selects `billing_ledger_lookup`.
- Bad final classification is wrong but plausible.
- Incident trace validates against schema.

Risk:

- The incident is too obvious or cartoonish to impress a senior reviewer.

### Phase 4: Build Replay And First-Divergence Diff

Goal: Compare baseline and incident traces and identify the first unacceptable divergence.

Files/artifacts likely created later:

- `src/traceforge/replay.py`
- `src/traceforge/diff.py`
- `reports/first_divergence_report.md`

Acceptance criteria:

- Diff reports Step 1 `requested_tool` as first divergence.
- Downstream differences are linked to the root divergence.
- Allowed nondeterministic fields are ignored or labeled.

Risk:

- Diff becomes a shallow JSON diff without causal labeling.

### Phase 5: Patch, Gate, And Report

Goal: Add patched fixture, generate incident timeline, and enforce a CI-style gate.

Files/artifacts likely created later:

- `fixtures/model_outputs/patched_prompt_route.json`
- `reports/incident_timeline.md`
- `reports/regression_gate_report.md`
- `src/traceforge/gate.py`

Acceptance criteria:

- Bad run fails the gate.
- Patched run passes the gate.
- Reports are regenerated from trace files.
- Demo can be run with one or two commands.

Risk:

- Gate checks become too weak and pass without proving replay value.

## 14. Demo Script

Five-minute demo path:

1. Run good workflow with `triage_route_prompt:v1`.
2. Show the append-only trace file with three clear steps.
3. Run bad workflow with `triage_route_prompt:v2_bad`.
4. Inspect that the final answer is plausible but wrong.
5. Replay the incident using cached model output and mocked tool responses.
6. Show first-divergence report: Step 1 selected `billing_ledger_lookup` instead of `service_metrics_lookup`.
7. Show incident timeline: wrong tool produced irrelevant evidence, causing wrong classification and missed escalation.
8. Apply patched prompt fixture `triage_route_prompt:v3_patch`.
9. Rerun regression gate.
10. Show bad run fails and patched run passes, with protected fields matching the baseline.

## 15. Portfolio Artifacts

Final public-facing artifacts should include:

- README
- architecture brief
- trace schema
- replay contract
- evaluation plan
- failure-mode register
- incident timeline report
- regression report
- demo script
- resume bullets

Optional later artifacts only after v1 works:

- LangGraph adapter note
- live-provider replay note
- tool fixture design note

## 16. Resume / Interview Story

### Resume Bullets

- Built TraceForge, a replay harness for LLM/tool pipelines that captures typed trace events, mocks tool responses, detects first-divergence failures, and turns incidents into CI-style regression gates.
- Designed a framework-neutral trace schema covering prompt/model/tool versions, input/output hashes, state transitions, replay status, determinism labels, latency, cost, and governance metadata.
- Seeded and reproduced a realistic wrong-tool-selection incident, then validated a patched prompt by comparing protected trace fields and blocking the bad release path.

### Short Interview Story

Production LLM incidents are hard to debug because the failure often lives between the prompt, model output, tool call, and state transition. I built TraceForge to make one of those incidents reproducible: a prompt regression caused an incident triage workflow to call the wrong tool, gather plausible but irrelevant evidence, and misclassify a real service outage as a billing issue. The system captured the trace, replayed the bad run with mocked tools, identified the first divergent step, and converted the fix into a release-blocking regression gate.

### Deeper Technical Walkthrough Angle

Walk through the replay contract. Explain why v1 uses cached/synthetic model outputs and mocked tool fixtures, how protected fields separate meaningful regressions from harmless variation, how the comparator finds first divergence instead of only final-output diffs, and how deterministic replay becomes governance evidence for prompt or model releases.

## 17. Non-Goals And Deferred Scope

Ruthless v1 non-goals:

- No dashboard.
- No full tracing backend.
- No enterprise auth or permissions.
- No multi-provider live replay.
- No full observability platform.
- No LangSmith or Langfuse clone.
- No broad framework abstraction until the v1 replay loop works.
- No vague agent platform framing.
- No root-cause hypothesis agent in v1.
- No vector database.
- No production deployment.
- No distributed tracing service.
- No large benchmark suite.
- No real customer data.
- No live tool calls during regression replay.
- No multi-incident corpus until the first seeded incident works.

Deferred scope:

- LangGraph adapter.
- Live-provider replay mode.
- Multiple workflow topologies.
- Human review queue.
- Richer determinism statistics.
- Browser or dashboard view.
- External CI provider integration.

## 18. Open Questions

No questions block implementation after this handoff.

Non-blocking decisions for later:

- Final public repo name.
- Whether the later demo should include optional LangGraph integration after the custom replay loop works.
- Whether to add live provider calls as a separate advanced mode after fixture-backed replay passes.

## 19. Recommendation

Proceed to implementation planning, not app implementation yet.

The next Codex task should be: create a bounded implementation plan for TraceForge v1 that defines the later file tree, commands, fixture names, trace/report artifacts, and acceptance tests without writing app code. After that plan is approved, implementation can begin with Phase 1: trace schema, replay contract, and incident fixtures.
