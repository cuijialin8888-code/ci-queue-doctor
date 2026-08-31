import json

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
