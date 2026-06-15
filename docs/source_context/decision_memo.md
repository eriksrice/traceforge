# Portfolio Selection Decision Memo

## Decision

- Primary decision: BUILD NOW - P060, TraceForge - LLM Pipeline Incident Replay Engine
- Backup candidate: HOLD - P006, Tool Side-Effect Sandbox & Idempotency Verifier
- Hold candidates: P061, P046, P072, P099, P065
- Reframe candidate: P047, Data Contract Release Gate with Semantic Drift Detection
- Dropped candidates: none at the final memo level; weaker candidates remain below finalist threshold or in NEEDS_REWRITE diagnostic status.

## Gate Outcome Summary

- ELIGIBLE: 74
- NEEDS_REWRITE: 26
- DISQUALIFIED: 0

## One-Line Read

Build P060 because it creates the strongest senior-level proof that Erik can make LLM systems observable, replayable, evaluated, and regression-safe without overbuilding an enterprise platform.

## Why The Winner Wins

- Winning candidate ID and title: P060 - TraceForge - LLM Pipeline Incident Replay Engine.
- Senior signal: It demonstrates production AI reliability, trace instrumentation, deterministic replay, failure-mode analysis, and release-gate thinking.
- Enterprise analogue: AI platform teams need to reproduce LLM/agent incidents, validate fixes, and prevent regressions before prompt or model changes ship.
- Expected architecture: Trace capture middleware, append-only event store, tool mock/replay layer, deterministic replay harness, diff classifier, incident timeline generator, and CI regression gate.
- Evaluation plan: Seed known incidents, assert replay reproduction, measure first-divergence detection, classify deterministic versus volatile steps, and run patched traces through a regression suite.
- Observability/governance angle: Every trace becomes an auditable event bundle with model/prompt/tool versions, latency, cost, intermediate outputs, replay status, and incident decision records.
- MVP scope: One 3-step LangGraph-style workflow, file-backed trace store, mocked tool replay, one seeded bad tool-call or prompt regression, diff report, incident timeline, and a CI-style failing gate.
- Risks: It can become too abstract if the incident is not vivid; deterministic replay must be honest about nondeterminism; tool mocking must be realistic enough to convince senior reviewers.
- Portfolio artifacts: Architecture brief, trace schema, replay contract, failure-mode register, incident report, regression report, demo script, and README with reproducible commands.
- Interview story: Production LLM failures are hard to reproduce, so Erik built the equivalent of incident replay infrastructure and turned traces into regression tests.

## Why The Runner-Up Loses

P006 is excellent but has more risk around mocked side effects and action semantics. P060 produces a cleaner first artifact: capture trace, replay trace, diff divergence, prove fix. It is easier to scope, easier to demo safely, and still carries strong AI platform depth.

## Required Reframes Or Verification

- Define the exact v1 workflow and seeded incident before architecture begins.
- Decide whether the replay target is a LangGraph workflow, a small custom tool-calling pipeline, or a framework-neutral trace schema.
- Keep model-provider dependencies optional; cached or synthetic outputs are acceptable for proving replay mechanics.
- Do not build a dashboard in v1. The artifacts should be files, tests, and reports.

## Project Selection Packet

```yaml
project_selection_packet:
  project_id: P060
  working_title: TraceForge - LLM Pipeline Incident Replay Engine
  gate_outcome: ELIGIBLE
  decision: BUILD NOW
  senior_signal_claim: Demonstrates production-grade LLM observability, deterministic replay, incident reconstruction, and regression gating.
  target_interview_story: I made AI pipeline incidents reproducible and turned replayed traces into release-blocking regression tests.
  core_user_or_buyer: AI platform engineering, LLM systems, MLOps, or production reliability teams.
  enterprise_pain: LLM incidents are hard to reproduce because prompts, model versions, tool outputs, and intermediate state are not captured in replayable form.
  likely_architecture: Trace middleware, append-only trace store, replay harness, tool mock layer, divergence classifier, incident timeline writer, CI gate.
  data_strategy: Synthetic multi-step traces with seeded failures, cached model outputs, and mocked tool responses; no sensitive data required.
  evaluation_strategy: Replay reproduction tests, first-divergence detection, determinism scoring, seeded regression suite, patched replay comparison.
  agent_or_state_complexity: Stateful trace lifecycle with replay modes, tool-call status, divergence labels, retry behavior, and incident timeline state.
  hardest_risks:
    - Keeping deterministic replay honest when LLM outputs are stochastic.
    - Avoiding dashboard sprawl before the core replay artifact works.
    - Making the seeded incident realistic enough for senior reviewers.
  build_scope_v1:
    - Instrument one 3-step tool-using workflow.
    - Capture typed trace events to a file-backed event store.
    - Replay with original inputs and mocked tool outputs.
    - Generate a step-level diff and incident timeline.
    - Run a CI-style regression check that fails on the seeded incident.
  deferred_scope:
    - Full tracing backend.
    - Browser dashboard.
    - Multi-provider live replay.
    - Enterprise auth and permissions.
  artifacts_to_create:
    - architecture_brief
    - trace_schema
    - replay_contract
    - evaluation_plan
    - failure_mode_register
    - incident_timeline_report
    - demo_script
  open_questions:
    - Which concrete workflow should produce the first incident trace?
    - Which failures should be seeded: prompt regression, wrong tool selection, tool timeout, or structured-output truncation?
    - Should the v1 use cached LLM outputs or live calls for the demo?
  recommended_next_operator: AI Systems Architect
```

## Next Action

Hand P060 to Project Architect for a bounded architecture brief that defines the v1 workflow, trace event schema, replay contract, seeded incident, and evaluation gates before any app code is written.
