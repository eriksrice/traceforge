# Batch 001 Workflow Findings

## Separation

The workflow created real separation. Weighted scoring separated top production-infrastructure projects from broad or payload-dependent concepts, and pairwise review further separated strong-on-paper ideas from build-now candidates. The clearest top cluster was P060, P006, P046, P047, P072, P099, P065, P061, P058, P094, P095, and P020.

## Weak Ideas

Weak ideas did not survive into the top bracket, but many were not structurally bad enough to disqualify. The hard gate therefore used NEEDS_REWRITE for concepts whose enterprise analogue was plausible but whose current framing leaned on indirect payloads, broad orchestration claims, or insufficiently bounded v1 scope.

## Strong Ideas Killed

Some strong ideas were held out of finalist comparison because the current framing needed rewrite, not because the core enterprise pattern was weak. Several knowledge reconciliation, prompt CI/CD, decision-support, migration, and side-effect safety variants could become eligible after a cleaner enterprise payload and narrower v1 are specified. This was intentional under the protocol: NEEDS_REWRITE candidates were scored diagnostically but not treated as finalist-ready.

## Scoring vs Pairwise

Scoring and pairwise mostly agreed on the top cluster but disagreed inside it. P006 scored extremely well but lost to P060 because the pairwise comparison favored a cleaner, safer, more inspectable v1. P072 beat some deeper graph ideas because build feasibility and deterministic evaluation were stronger. P061 rose in pairwise because rare agent-runtime signal mattered more than broad adequacy.

## Buildability

The winning project is actually buildable if v1 stays narrow: one 3-step tool-using workflow, one trace schema, one replay harness, one seeded incident, one diff report, and one CI-style gate. The risk is not technical impossibility; it is scope creep into a full observability platform.

## Batch Size

One hundred ideas was useful for stress-testing the workflow but too many for the current protocol without an explicit dedupe/cluster step. The batch contained many near-duplicates, causing scoring effort to repeat the same decision patterns.

## Recommended Small Future Patches

- Add a pre-scoring cluster/dedupe pass that groups near-duplicate concepts while preserving neutral candidate IDs.
- Add an optional payload-professionalism check to the hard gate so strong architectures with distracting payloads become NEEDS_REWRITE consistently.
- Add a top-cluster calibration note to scoring so repeated categories do not all crowd the same score band.
- Keep the rubric unchanged for now; the issue was workflow volume and duplicate handling, not a scoring-schema failure.
