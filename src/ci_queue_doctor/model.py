from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def parse_timestamp(value: Any) -> datetime | None:
    """Parse a GitHub ISO-8601 timestamp without trusting malformed input."""

    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


@dataclass(frozen=True)
class WorkflowRun:
    run_id: int
    name: str
    status: str
    conclusion: str | None
    event: str | None
    branch: str | None
    head_sha: str | None
    created_at: datetime | None
    updated_at: datetime | None
    html_url: str | None
    run_attempt: int | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> WorkflowRun:
        raw_id = data.get("id")
        try:
            run_id = int(raw_id)
        except (TypeError, ValueError):
            run_id = 0
        return cls(
            run_id=run_id,
            name=_text(data.get("name")) or "(unnamed workflow)",
            status=_text(data.get("status")) or "unknown",
            conclusion=_text(data.get("conclusion")),
            event=_text(data.get("event")),
            branch=_text(data.get("head_branch")),
            head_sha=_text(data.get("head_sha")),
            created_at=parse_timestamp(data.get("created_at")),
            updated_at=parse_timestamp(data.get("updated_at")),
            html_url=_text(data.get("html_url")),
            run_attempt=(
                int(data["run_attempt"]) if isinstance(data.get("run_attempt"), int) else None
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.run_id,
            "name": self.name,
            "status": self.status,
            "conclusion": self.conclusion,
            "event": self.event,
            "branch": self.branch,
            "head_sha": self.head_sha,
            "created_at": self.created_at.isoformat().replace("+00:00", "Z")
            if self.created_at
            else None,
            "updated_at": self.updated_at.isoformat().replace("+00:00", "Z")
            if self.updated_at
            else None,
            "run_attempt": self.run_attempt,
            "html_url": self.html_url,
        }


@dataclass(frozen=True)
class Job:
    job_id: int
    name: str
    status: str
    conclusion: str | None
    started_at: datetime | None
    completed_at: datetime | None
    html_url: str | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Job:
        raw_id = data.get("id")
        try:
            job_id = int(raw_id)
        except (TypeError, ValueError):
            job_id = 0
        return cls(
            job_id=job_id,
            name=_text(data.get("name")) or "(unnamed job)",
            status=_text(data.get("status")) or "unknown",
            conclusion=_text(data.get("conclusion")),
            started_at=parse_timestamp(data.get("started_at")),
            completed_at=parse_timestamp(data.get("completed_at")),
            html_url=_text(data.get("html_url")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.job_id,
            "name": self.name,
            "status": self.status,
            "conclusion": self.conclusion,
            "started_at": self.started_at.isoformat().replace("+00:00", "Z")
            if self.started_at
            else None,
            "completed_at": self.completed_at.isoformat().replace("+00:00", "Z")
            if self.completed_at
            else None,
            "html_url": self.html_url,
        }


@dataclass(frozen=True)
class Finding:
    code: str
    level: str
    title: str
    message: str
    evidence: tuple[str, ...]
    next_step: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "level": self.level,
            "title": self.title,
            "message": self.message,
            "evidence": list(self.evidence),
            "next_step": self.next_step,
        }


@dataclass(frozen=True)
class Report:
    schema_version: str
    repo: str
    default_branch: str | None
    observed_at: datetime
    run: WorkflowRun
    jobs: tuple[Job, ...]
    queue_age_seconds: int | None
    job_status_counts: dict[str, int]
    findings: tuple[Finding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tool": {"name": "ci-queue-doctor", "version": "0.1.0"},
            "repo": self.repo,
            "default_branch": self.default_branch,
            "observed_at": self.observed_at.isoformat().replace("+00:00", "Z"),
            "run": self.run.to_dict(),
            "queue_age_seconds": self.queue_age_seconds,
            "job_status_counts": dict(sorted(self.job_status_counts.items())),
            "jobs": [job.to_dict() for job in self.jobs],
            "findings": [finding.to_dict() for finding in self.findings],
            "safety": {
                "read_only": True,
                "network_methods": ["GET"],
                "workflows_executed": False,
                "secrets_printed": False,
            },
        }
