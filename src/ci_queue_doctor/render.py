from __future__ import annotations

import json
from typing import Any

from .model import Finding, Report


def render_json(report: Report) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _level_icon(level: str) -> str:
    return {"error": "ERROR", "warning": "WARN", "info": "INFO"}.get(level, level.upper())


def _finding_lines(finding: Finding, markdown: bool = False) -> list[str]:
    prefix = "- " if markdown else "  "
    lines = [f"{prefix}[{_level_icon(finding.level)}] {finding.code}: {finding.title}"]
    lines.append(f"{prefix}  {finding.message}")
    for evidence in finding.evidence:
        lines.append(f"{prefix}  Evidence: {evidence}")
    lines.append(f"{prefix}  Next: {finding.next_step}")
    return lines


def render_text(report: Report) -> str:
    run = report.run
    queue_age = report.queue_age_seconds if report.queue_age_seconds is not None else "unknown"
    job_summary = ", ".join(
        f"{key}={value}" for key, value in sorted(report.job_status_counts.items())
    ) or "none"
    lines = [
        "ci-queue-doctor — read-only GitHub Actions evidence",
        f"Repository: {report.repo}",
        f"Run:        {run.run_id} ({run.name})",
        f"Status:     {run.status} / {run.conclusion or 'not concluded'}",
        f"Event:      {run.event or 'unknown'}",
        f"Branch:     {run.branch or 'unknown'}",
        f"Queue age:  {queue_age} seconds",
        f"Jobs:       {sum(report.job_status_counts.values())} ({job_summary})",
        "",
        "Findings:",
    ]
    if report.findings:
        for finding in report.findings:
            lines.extend(_finding_lines(finding))
    else:
        lines.append("  [OK] No actionable queue finding was observed.")
    lines.extend(
        [
            "",
            (
                "Safety: GET-only; workflows are not executed, retried, canceled, "
                "dispatched, or modified."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def render_markdown(report: Report) -> str:
    run = report.run
    queue_age = report.queue_age_seconds if report.queue_age_seconds is not None else "unknown"
    job_statuses = json.dumps(report.job_status_counts, ensure_ascii=False, sort_keys=True)
    lines = [
        "# CI Queue Doctor report",
        "",
        f"- Repository: `{report.repo}`",
        f"- Run: `{run.run_id}` — {run.name}",
        f"- Status: `{run.status}` / `{run.conclusion or 'not concluded'}`",
        f"- Event / branch: `{run.event or 'unknown'}` / `{run.branch or 'unknown'}`",
        f"- Queue age: `{queue_age}` seconds",
        f"- Job statuses: `{job_statuses}`",
        "",
        "## Findings",
        "",
    ]
    if report.findings:
        for finding in report.findings:
            lines.extend(_finding_lines(finding, markdown=True))
    else:
        lines.append("No actionable queue finding was observed.")
    lines.extend(
        [
            "",
            (
                "> Safety: this report is GET-only. It never executes, retries, cancels, "
                "dispatches, or modifies workflows."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def render_sarif(report: Report) -> str:
    rules: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for finding in report.findings:
        rules.append(
            {
                "id": finding.code,
                "name": finding.title,
                "shortDescription": {"text": finding.title},
                "fullDescription": {"text": finding.message},
                "help": {"text": finding.next_step},
            }
        )
        results.append(
            {
                "ruleId": finding.code,
                "level": {"info": "note", "warning": "warning", "error": "error"}.get(
                    finding.level, "note"
                ),
                "message": {"text": f"{finding.message} Evidence: {'; '.join(finding.evidence)}"},
            }
        )
    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "ci-queue-doctor", "version": "0.1.0", "rules": rules}},
                "results": results,
                "properties": {"repo": report.repo, "run_id": report.run.run_id, "read_only": True},
            }
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
