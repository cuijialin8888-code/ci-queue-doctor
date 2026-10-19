import json
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from ci_queue_doctor.diagnose import diagnose
from ci_queue_doctor.model import Finding
from ci_queue_doctor.render import render_json, render_markdown, render_text


class MarkdownTests(unittest.TestCase):
    def report(self):
        return diagnose(
            repo="example/project",
            default_branch="main",
            run_data={"id": 123, "name": "CI", "status": "completed", "conclusion": "success"},
            jobs_data=[],
            observed_at=datetime(2026, 10, 19, tzinfo=timezone.utc),
        )

    def test_run_fields_cannot_add_html_headings_or_links(self):
        value = "CI`</code><img src=x>\r\n# injected\n[forged](https://example.com)"
        report = self.report()
        report = replace(
            report,
            run=replace(
                report.run, name=value, status=value, conclusion=value, event=value, branch=value
            ),
            job_status_counts={value: 1},
        )
        rendered = render_markdown(report)
        self.assertNotIn("<img", rendered)
        self.assertNotIn("\r", rendered)
        self.assertNotIn("\n# injected", rendered)
        self.assertNotIn("[forged](https://example.com)", rendered.splitlines()[3])
        self.assertEqual(
            len(rendered.splitlines()), len(render_markdown(self.report()).splitlines())
        )

    def test_finding_fields_cannot_add_report_structure(self):
        value = "**forged** [link](https://example.com) <script>x</script>\r\n# injected"
        report = replace(
            self.report(),
            findings=(Finding("CQD001", "warning", value, value, (value,), value),),
        )
        rendered = render_markdown(report)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("\n# injected", rendered)
        self.assertNotIn("**forged**", rendered)
        self.assertNotIn("[link](https://example.com)", rendered)
        self.assertIn("[WARN] CQD001", rendered)

    def test_text_and_json_keep_original_values(self):
        value = "CI`<tag>&\n# original"
        report = self.report()
        report = replace(report, run=replace(report.run, name=value, branch=value))
        self.assertIn(value, render_text(report))
        data = json.loads(render_json(report))
        self.assertEqual(data["run"]["name"], value)
        self.assertEqual(data["run"]["branch"], value)
