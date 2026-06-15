from datetime import datetime, timezone

from traceforge.hashing import canonical_json, stable_hash


def test_stable_hash_ignores_dict_order() -> None:
    left = {"b": 2, "a": {"z": 1, "y": [3, 2, 1]}}
    right = {"a": {"y": [3, 2, 1], "z": 1}, "b": 2}

    assert stable_hash(left) == stable_hash(right)


def test_canonical_json_serializes_datetimes() -> None:
    payload = {"at": datetime(2026, 6, 12, 15, 42, tzinfo=timezone.utc)}

    assert canonical_json(payload) == '{"at":"2026-06-12T15:42:00+00:00"}'
