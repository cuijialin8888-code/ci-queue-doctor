from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from .model import Finding, Job, Report, WorkflowRun


def _age_seconds(run: WorkflowRun, observed_at: datetime) -> int | None:
    if run.created_at is None:
        return None
    return max(0, int((observed_at - run.created_at).total_seconds()))


def _minutes(seconds: int | None) -> str:
    if seconds is None:
        return "unknown"
    return f"{seconds / 60:.1f} min"


def diagnose(
    *,
    repo: str,
    default_branch: str | None,
    run_data: dict[str, Any],
    jobs_data: Iterable[dict[str, Any]],
    threshold_minutes: float = 10.0,
    observed_at: datetime | None = None,
) -> Report:
    """Classify observable queue evidence without guessing GitHub internals."""

    if threshold_minutes <= 0:
        raise ValueError("threshold_minutes must be positive")
    observed = (observed_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    run = WorkflowRun.from_api(run_data)
    jobs = tuple(Job.from_api(job) for job in jobs_data)
    counts = dict(Counter(job.status.lower() for job in jobs))
    age = _age_seconds(run, observed)
    created_at = run.created_at.isoformat() if run.created_at else "missing"
    threshold_seconds = int(threshold_minutes * 60)
    status = run.status.lower()
    queued_jobs = counts.get("queued", 0)
    waiting_jobs = counts.get("waiting", 0)
    findings: list[Finding] = []

    if status == "queued":
        if age is not None and age >= threshold_seconds:
            findings.append(
                Finding(
                    "CQD001",
                    "warning",
                    "Workflow run exceeded the queue threshold",
                    (
                        f"The run has been queued for {_minutes(age)} "
                        f"(threshold {threshold_minutes:g} min)."
                    ),
                    (
                        f"run.status={run.status}",
                        f"run.created_at={created_at}",
                        f"queue_age_seconds={age}",
                    ),
                    (
                        "Check concurrency, environment approvals, runner availability, and the "
                        "Actions UI; this tool cannot see GitHub's internal scheduler reason."
                    ),
                )
            )
        if not jobs:
            findings.append(
                Finding(
                    "CQD002",
                    "info",
                    "No job records are visible yet",
                    "GitHub has returned a queued run without job records.",
                    ("jobs.count=0", "run.status=queued"),
                    (
                        "Wait for a short interval and inspect the run's Checks/Actions page "
                        "if it remains queued."
                    ),
                )
            )
        elif queued_jobs:
            level = "warning" if age is not None and age >= threshold_seconds else "info"
            findings.append(
                Finding(
                    "CQD003",
                    level,
                    "Jobs are waiting for a runner",
                    f"{queued_jobs} job(s) report status=queued while the workflow run is queued.",
                    (f"job_status_counts={counts}",),
                    (
                        "Check runner labels, capacity, concurrency, and repository Actions "
                        "settings; no job is executed by this report."
                    ),
                )
            )

    elif status == "in_progress":
        if queued_jobs:
            level = "warning" if age is not None and age >= threshold_seconds else "info"
            findings.append(
                Finding(
                    "CQD004",
                    level,
                    "Workflow is running with queued jobs",
                    f"The run is in progress but {queued_jobs} job(s) remain queued.",
                    (f"run.status={run.status}", f"job_status_counts={counts}"),
                    (
                        "Check matrix dependencies, concurrency, runner labels, and environment "
                        "gates before changing the workflow."
                    ),
                )
            )
        if waiting_jobs:
            findings.append(
                Finding(
                    "CQD005",
                    "info",
                    "A job is in a waiting state",
                    (
                        f"{waiting_jobs} job(s) report status=waiting; the API does not identify "
                        "the precise gate reason."
                    ),
                    (f"job_status_counts={counts}",),
                    "Inspect the job details for approvals, concurrency, or manual gates.",
                )
            )

    elif status == "completed":
        if run.conclusion not in {"success", "skipped", "neutral"}:
            findings.append(
                Finding(
                    "CQD010",
                    "warning",
                    "Workflow completed without a successful conclusion",
                    f"The run completed with conclusion={run.conclusion or 'missing'}.",
                    (f"run.status={run.status}", f"run.conclusion={run.conclusion or 'missing'}"),
                    (
                        "Open the run's failed job logs; this report does not retry or modify "
                        "the workflow."
                    ),
                )
            )
    else:
        findings.append(
            Finding(
                "CQD099",
                "warning",
                "GitHub returned an unfamiliar workflow status",
                f"The run status is {run.status!r}; queue classification is limited.",
                (f"run.status={run.status}",),
                (
                    "Inspect the raw run in GitHub before taking action; preserve the evidence "
                    "for a bug report if needed."
                ),
            )
        )

    return Report(
        schema_version="1",
        repo=repo,
        default_branch=default_branch,
        observed_at=observed,
        run=run,
        jobs=jobs,
        queue_age_seconds=age,
        job_status_counts=counts,
        findings=tuple(findings),
    )
