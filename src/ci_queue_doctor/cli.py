from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from . import __version__
from .diagnose import diagnose
from .github import GitHubApiError, GitHubClient
from .render import render_json, render_markdown, render_sarif, render_text


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci-queue-doctor",
        description="Read-only evidence for a GitHub Actions run that is queued or waiting.",
    )
    parser.add_argument("--repo", required=True, help="GitHub repository in OWNER/REPOSITORY form")
    parser.add_argument("--run", type=int, help="Inspect this workflow run ID")
    parser.add_argument("--branch", help="Filter latest-run selection to this branch")
    parser.add_argument(
        "--limit", type=int, default=20, help="Latest runs to request (1-100; default: 20)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        metavar="MINUTES",
        help="Queue age at which a finding becomes a warning (default: 10)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "markdown", "sarif"),
        default="text",
        help="Report format",
    )
    parser.add_argument(
        "--fail-on",
        choices=("none", "warning", "error"),
        default="none",
        help="Exit 1 when at least this severity is present",
    )
    parser.add_argument("--token", help=argparse.SUPPRESS)
    parser.add_argument(
        "--token-stdin",
        action="store_true",
        help="Read a GitHub token from stdin; prefer GH_TOKEN for automation",
    )
    parser.add_argument(
        "--timeout", type=float, default=15.0, help="HTTP timeout in seconds (default: 15)"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _token(args: argparse.Namespace) -> str | None:
    if args.token_stdin:
        value = sys.stdin.read().strip()
        return value or None
    return args.token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def _render(report, fmt: str) -> str:
    return {
        "text": render_text,
        "json": render_json,
        "markdown": render_markdown,
        "sarif": render_sarif,
    }[fmt](report)


def _fail_rank(level: str) -> int:
    return {"none": 99, "info": 0, "warning": 1, "error": 2}[level]


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.timeout <= 0 or args.threshold <= 0:
        print("error: --timeout and --threshold must be positive", file=sys.stderr)
        return 2
    try:
        client = GitHubClient(token=_token(args), timeout=args.timeout)
        repo_data = client.get_repo(args.repo)
        default_branch = repo_data.get("default_branch") if isinstance(repo_data, dict) else None
        if args.run is not None:
            run_data = client.get_run(args.repo, args.run)
        else:
            branch = args.branch or default_branch
            runs = client.list_runs(args.repo, branch=branch, limit=args.limit)
            if not runs:
                raise GitHubApiError("No workflow runs matched the selected repository/branch.")
            run_data = runs[0]
        raw_id = run_data.get("id") if isinstance(run_data, dict) else None
        try:
            run_id = int(raw_id)
        except (TypeError, ValueError):
            raise GitHubApiError("GitHub returned a workflow run without a valid ID.") from None
        run_detail = client.get_run(args.repo, run_id)
        jobs = client.list_jobs(args.repo, run_id)
        report = diagnose(
            repo=args.repo,
            default_branch=default_branch,
            run_data=run_detail,
            jobs_data=jobs,
            threshold_minutes=args.threshold,
        )
        print(_render(report, args.format), end="")
        if args.fail_on != "none" and any(
            _fail_rank(finding.level) >= _fail_rank(args.fail_on) for finding in report.findings
        ):
            return 1
        return 0
    except (GitHubApiError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
