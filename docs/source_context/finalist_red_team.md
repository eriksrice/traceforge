# Batch 001 Finalist Red Team

## Finalist Reviews

### P060 - TraceForge - LLM Pipeline Incident Replay Engine

- Strongest case for building: Best blend of senior AI platform signal, observability, deterministic replay, incident analysis, and testable MVP scope.
- Why it might fail to impress: If it is only log capture plus before/after output diffs, a Staff-level reviewer may see a thin tracing demo rather than incident reconstruction infrastructure.
- Generic demo risk: medium. Mitigation: show first-divergence detection, mocked tool replay, determinism scoring, and CI regression use.
- Data risk: low. Synthetic LangGraph traces are acceptable if failure cases are realistic and seeded.
- Evaluation risk: medium. The project must define replay determinism, divergence severity, and regression thresholds explicitly.
- Scope risk: medium. Keep v1 to one 3-step pipeline, one trace store, one replay mode, and one report.
- Interview credibility risk: low. The story is clearly senior if artifacts are real.
- What must be true: Replay must be deterministic enough to reproduce a seeded incident and prove a fix.
- Decision after red-team: BUILD NOW.

### P006 - Tool Side-Effect Sandbox & Idempotency Verifier

- Strongest case for building: Very practical production-agent safety story with clear side-effect, idempotency, retry, and compensation artifacts.
- Why it might fail to impress: If external APIs are all mocked too casually, the demo may feel hypothetical. If real money/actions are implied, professional risk rises.
- Generic demo risk: low. Tool safety is underrepresented and production-relevant.
- Data risk: low. Synthetic support/claims workflows are enough.
- Evaluation risk: medium. Needs hard assertions for duplicate writes, rollback, and unsafe action blocking.
- Scope risk: medium-high. Side-effect semantics can sprawl across many action types.
- Interview credibility risk: low. Strong if it shows blocked duplicate action and event ledger replay.
- What must be true: The v1 must treat tool contracts and idempotency as first-class state, not after-the-fact logging.
- Decision after red-team: HOLD.

### P046 - LLM Inference SLO Tracker with Shadow-Mode Evaluator

- Strongest case for building: Directly maps to model upgrade risk and production EvalOps; easy to explain to AI platform teams.
- Why it might fail to impress: It may look like another eval harness unless it shows SLO budgets, structured traces, and disagreement routing.
- Generic demo risk: medium. Many portfolios now claim eval gates.
- Data risk: low-medium. Needs a credible trace corpus with realistic tasks, not arbitrary benchmark prompts.
- Evaluation risk: medium. Must avoid evaluator-vibes by using typed contracts and deterministic checks.
- Scope risk: low-medium. Feasible if limited to one task family and one challenger.
- Interview credibility risk: medium. Strong, but P060 tells a richer incident story.
- What must be true: The shadow-mode report must catch a seeded regression that aggregate averages miss.
- Decision after red-team: HOLD.

### P047 - Data Contract Release Gate with Semantic Drift Detection

- Strongest case for building: Enterprise pain is obvious, build path is clear, and artifacts are concrete.
- Why it might fail to impress: Data contract gates are familiar; semantic drift via embeddings alone may seem shallow or brittle.
- Generic demo risk: medium-high. Needs a sharper angle than schema validation plus drift report.
- Data risk: low. Public/synthetic datasets work well.
- Evaluation risk: low-medium. Seeded drift cases are straightforward.
- Scope risk: low. Very buildable.
- Interview credibility risk: medium. It may read more senior data engineering than senior applied AI unless reframed with downstream model/metric blast radius.
- What must be true: It should compile contracts to executable tests and prove semantic breaks that schema checks miss.
- Decision after red-team: REFRAME.

## Red-Team Verdict

P060 survives scrutiny best. P006 is the best backup and may be strategically stronger if the portfolio needs an agent-safety flagship. P046 is credible but partially overlaps with P060. P047 is buildable and enterprise-serious but needs a sharper differentiator before it deserves BUILD NOW.
