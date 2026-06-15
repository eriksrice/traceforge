from traceforge.tracing import TraceWriter, read_trace
from traceforge.workflow import run_workflow


def test_trace_writer_round_trips_jsonl(tmp_path) -> None:
    result = run_workflow("baseline", write_trace=False)
    trace_path = tmp_path / "baseline_good.jsonl"

    TraceWriter(trace_path).write_events(result.events)
    loaded = read_trace(trace_path)

    assert len(loaded) == len(result.events)
    assert loaded[0].trace_id == result.trace_id
    assert loaded[-1].step_index == 3
