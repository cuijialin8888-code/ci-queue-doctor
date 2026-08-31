from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class GitHubApiError(RuntimeError):
    """A safe, user-facing description of a read-only GitHub API failure."""


class GitHubClient:
    """Small GET-only client for the public GitHub REST API."""

    def __init__(
        self,
        token: str | None = None,
        timeout: float = 15.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self._token = token.strip() if token and token.strip() else None
        self._timeout = timeout
        self._opener = opener

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        request = Request(
            f"https://api.github.com{path}{query}",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "ci-queue-doctor/0.1.0",
                **({"Authorization": f"Bearer {self._token}"} if self._token else {}),
            },
            method="GET",
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 401:
                raise GitHubApiError(
                    "GitHub API rejected the token (401). Check GH_TOKEN."
                ) from None
            if exc.code == 403:
                raise GitHubApiError(
                    "GitHub API denied this read (403), possibly due to rate limiting "
                    "or permissions."
                ) from None
            if exc.code == 404:
                raise GitHubApiError(
                    "Repository, workflow run, or jobs were not found (404)."
                ) from None
            raise GitHubApiError(f"GitHub API returned HTTP {exc.code}.") from None
        except URLError as exc:
            raise GitHubApiError(f"Could not reach api.github.com: {exc.reason}") from None
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise GitHubApiError("GitHub API returned invalid JSON.") from exc

    @staticmethod
    def _check_repo(repo: str) -> str:
        normalized = repo.strip()
        if not _REPO_RE.fullmatch(normalized):
            raise GitHubApiError("--repo must be in OWNER/REPOSITORY form.")
        return normalized

    def get_repo(self, repo: str) -> dict[str, Any]:
        return self._get(f"/repos/{self._check_repo(repo)}")

    def list_runs(
        self, repo: str, branch: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        if limit < 1 or limit > 100:
            raise GitHubApiError("--limit must be between 1 and 100.")
        data = self._get(
            f"/repos/{self._check_repo(repo)}/actions/runs",
            {"per_page": str(limit), **({"branch": branch} if branch else {})},
        )
        runs = data.get("workflow_runs") if isinstance(data, dict) else None
        return runs if isinstance(runs, list) else []

    def get_run(self, repo: str, run_id: int) -> dict[str, Any]:
        if run_id < 1:
            raise GitHubApiError("--run must be a positive integer.")
        return self._get(f"/repos/{self._check_repo(repo)}/actions/runs/{run_id}")

    def list_jobs(self, repo: str, run_id: int) -> list[dict[str, Any]]:
        if run_id < 1:
            raise GitHubApiError("Workflow run ID must be a positive integer.")
        data = self._get(
            f"/repos/{self._check_repo(repo)}/actions/runs/{run_id}/jobs",
            {"per_page": "100"},
        )
        jobs = data.get("jobs") if isinstance(data, dict) else None
        return jobs if isinstance(jobs, list) else []
