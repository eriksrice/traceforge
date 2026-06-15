# Failure Modes

## System Failure Modes

- Trace events miss required fields.
- Hashes are unstable or computed after mutation.
- Mocked tool responses are unrealistic.
- Replay accidentally calls live tools.
- Comparator only diffs final output.
- Harmless wording changes are treated as blocking.
- Volatile steps are treated as deterministic.
- State transition metadata is too thin.
- Gate passes because protected fields are incomplete.

## Portfolio Failure Modes

- The project looks like simple log capture.
- The incident feels staged.
- Scope creeps into a dashboard or platform.
- LangGraph or provider integrations arrive before replay mechanics work.
- Reports describe the incident without proving reproduction.

## V1 Mitigations

- Typed Pydantic models reject missing required trace fields.
- Stable hashing canonicalizes fixture and state payloads.
- The demo uses realistic service telemetry and plausible billing evidence.
- Regression replay uses cached model fixtures and mocked tool fixtures only.
- The comparator reports Step 1 `requested_tool` as the first blocking divergence.
- Downstream differences are labeled as effects of the first divergence.
- The gate passes only when the bad run fails for the expected reason and the patched run matches baseline protected fields.
- Reports are generated from trace and comparison artifacts.
