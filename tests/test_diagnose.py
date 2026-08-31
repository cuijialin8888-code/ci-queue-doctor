import json
from datetime import datetime, timezone

from ci_queue_doctor.diagnose import diagnose
from ci_queue_doctor.render import render_json, render_markdown, render_sarif, render_text

OBSERVED = datetime(2026, 8, 31, 12, 10, tzinfo=timezone.utc)


def run_data(status="queued", conclusion=None):
    return {
        "id": 123,
        "name": "CI",
        "status": status,
        "conclusion": conclusion,
        "event": "push",
        "head_branch": "main",
        "head_sha": "a" * 40,
        "created_at": "2026-08-31T12:00:00Z",
        "updated_at": "2026-08-31T12:05:00Z",
        "run_attempt": 1,
        "html_url": "https://github.com/example/project/actions/runs/123",
    }


def job_data(status="queued"):
    return {
        "id": 456,
        "name": "ubuntu / Python 3.13",
        "status": status,
        "conclusion": None,
        "started_at": None,
        "completed_at": None,
        "html_url": "https://github.com/example/project/actions/runs/123/job/456",
    }


def test_stale_queue_has_evidence_and_counts():
    report = diagnose(
        repo="example/project",
        default_branch="main",
        run_data=run_data(),
        jobs_data=[job_data(), {**job_data(), "id": 457, "status": "waiting"}],
        threshold_minutes=5,
        observed_at=OBSERVED,
    )

    assert report.queue_age_seconds == 600
    assert report.job_status_counts == {"queued": 1, "waiting": 1}
    assert [finding.code for finding in report.findings] == ["CQD001", "CQD003"]
    assert report.findings[0].level == "warning"
    assert report.to_dict()["safety"] == {
        "read_only": True,
        "network_methods": ["GET"],
        "workflows_executed": False,
        "secrets_printed": False,
    }


def test_completed_success_is_quiet():
    report = diagnose(
        repo="example/project",
        default_branch="main",
        run_data=run_data(status="completed", conclusion="success"),
        jobs_data=[{**job_data(), "status": "completed", "conclusion": "success"}],
        observed_at=OBSERVED,
    )

    assert report.findings == ()
    assert "No actionable queue finding" in render_text(report)


def test_renderers_are_machine_readable_and_do_not_expose_tokens():
    report = diagnose(
        repo="example/project",
        default_branch="main",
        run_data=run_data(),
        jobs_data=[],
        observed_at=OBSERVED,
    )
    for rendered in (render_json(report), render_markdown(report), render_sarif(report)):
        assert "gho_" not in rendered
    assert json.loads(render_json(report))["run"]["id"] == 123
    assert json.loads(render_sarif(report))["version"] == "2.1.0"


def test_in_progress_queued_job_is_reported():
    report = diagnose(
        repo="example/project",
        default_branch="main",
        run_data=run_data(status="in_progress"),
        jobs_data=[job_data()],
        threshold_minutes=20,
        observed_at=OBSERVED,
    )

    assert [(item.code, item.level) for item in report.findings] == [("CQD004", "info")]
