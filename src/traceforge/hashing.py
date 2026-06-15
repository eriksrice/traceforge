"""Stable hashing utilities for deterministic trace and replay artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any


def canonicalize(value: Any) -> Any:
    """Return a JSON-serializable value with deterministic ordering."""

    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json", exclude_none=False)

    if isinstance(value, dict):
        return {str(key): canonicalize(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    if isinstance(value, set):
        return [canonicalize(item) for item in sorted(value, key=repr)]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    return value


def canonical_json(value: Any) -> str:
    """Serialize a value as stable, compact JSON."""

    return json.dumps(
        canonicalize(value),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def stable_hash(value: Any, *, prefix: str = "sha256") -> str:
    """Return a stable SHA-256 hash for JSON-like values."""

    payload = canonical_json(value).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    if prefix:
        return f"{prefix}:{digest}"
    return digest


def hash_text(value: str, *, prefix: str = "sha256") -> str:
    """Hash raw text without JSON string quoting."""

    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    if prefix:
        return f"{prefix}:{digest}"
    return digest
