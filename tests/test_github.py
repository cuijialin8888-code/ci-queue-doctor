import json
from urllib.error import HTTPError

import pytest

from ci_queue_doctor.github import GitHubApiError, GitHubClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_client_uses_get_and_bearer_token():
    seen = {}

    def opener(request, timeout):
        seen["method"] = request.method
        seen["url"] = request.full_url
        seen["authorization"] = request.get_header("Authorization")
        seen["timeout"] = timeout
        return FakeResponse({"default_branch": "main"})

    result = GitHubClient(token="secret", timeout=7, opener=opener).get_repo("a/b")

    assert result["default_branch"] == "main"
    assert seen == {
        "method": "GET",
        "url": "https://api.github.com/repos/a/b",
        "authorization": "Bearer secret",
        "timeout": 7,
    }


def test_client_rejects_invalid_repo_without_network():
    def never_called(*_args, **_kwargs):
        raise AssertionError("network must not be called")

    with pytest.raises(GitHubApiError, match="OWNER/REPOSITORY"):
        GitHubClient(opener=never_called).get_repo("not a repo")


@pytest.mark.parametrize(
    ("workflow", "segment"),
    [(" ci.yml ", "ci.yml"), ("12345", "12345"), ("build #1.yml", "build%20%231.yml")],
)
def test_list_runs_can_filter_by_workflow_file_or_id(workflow, segment):
    seen = {}

    def opener(request, timeout):
        seen["url"] = request.full_url
        return FakeResponse({"workflow_runs": [{"id": 123, "workflow_id": 456}]})

    result = GitHubClient(opener=opener).list_runs(
        "a/b", branch="main", limit=7, workflow=workflow
    )

    assert result == [{"id": 123, "workflow_id": 456}]
    assert seen["url"] == (
        f"https://api.github.com/repos/a/b/actions/workflows/{segment}/runs?per_page=7&branch=main"
    )


@pytest.mark.parametrize("workflow", [None, "", "   "])
def test_list_runs_without_workflow_keeps_repository_endpoint(workflow):
    def opener(request, timeout):
        assert request.method == "GET"
        assert request.full_url == (
            "https://api.github.com/repos/a/b/actions/runs?per_page=20&branch=feature%2Ffix"
        )
        return FakeResponse({"workflow_runs": [{"id": 789}]})

    result = GitHubClient(opener=opener).list_runs(
        "a/b", branch="feature/fix", workflow=workflow
    )
    assert result == [{"id": 789}]


def test_unknown_workflow_is_an_error_instead_of_returning_unrelated_runs():
    def opener(request, timeout):
        if "/actions/workflows/missing.yml/runs" in request.full_url:
            raise HTTPError(request.full_url, 404, "Not Found", {}, None)
        return FakeResponse({"workflow_runs": [{"id": 999}]})

    with pytest.raises(GitHubApiError, match="404"):
        GitHubClient(opener=opener).list_runs("a/b", workflow="missing.yml")
