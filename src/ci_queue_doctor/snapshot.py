"""Bounded offline replay of public workflow observations."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

MAX_SNAPSHOT_BYTES = 5_000_000


def load_snapshot(path: Path) -> tuple[dict[str, Any], datetime]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("snapshot must be a regular JSON file, not a symbolic link")
    with path.open("rb") as handle:
        raw = handle.read(MAX_SNAPSHOT_BYTES + 1)
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise ValueError("snapshot exceeds the 5 MB size limit")
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("snapshot is not valid UTF-8 JSON") from exc
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        raise ValueError("snapshot must be an object with schemaVersion 1")
    if not isinstance(data.get("repo"), str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+", data["repo"]
    ):
        raise ValueError("snapshot repo must be OWNER/REPOSITORY")
    if not isinstance(data.get("run"), dict):
        raise ValueError("snapshot run must be an object")
    if not isinstance(data.get("jobs"), list) or any(
        not isinstance(job, dict) for job in data["jobs"]
    ):
        raise ValueError("snapshot jobs must be an array of objects")
    if data.get("defaultBranch") is not None and not isinstance(data["defaultBranch"], str):
        raise ValueError("snapshot defaultBranch must be a string or null")
    captured = data.get("capturedAt")
    if not isinstance(captured, str):
        raise ValueError("snapshot capturedAt must be an ISO 8601 timestamp with timezone")
    try:
        observed = datetime.fromisoformat(captured.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("snapshot capturedAt is not a valid ISO 8601 timestamp") from exc
    if observed.tzinfo is None:
        raise ValueError("snapshot capturedAt must include a timezone")
    return data, observed
