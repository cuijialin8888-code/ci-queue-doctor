import json

from ci_queue_doctor import cli


class FakeClient:
    def __init__(self, **_kwargs):
        pass

    def get_repo(self, _repo):
        return {"default_branch": "main"}

    def list_runs(self, _repo, branch, limit):
        assert branch == "main"
        assert limit == 20
        return [{"id": 123}]

    def get_run(self, _repo, _run_id):
        return {
            "id": 123,
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "created_at": "2026-08-31T12:00:00Z",
            "updated_at": "2026-08-31T12:01:00Z",
        }

    def list_jobs(self, _repo, _run_id):
        return []


def test_cli_latest_run_json(monkeypatch, capsys):
    monkeypatch.setattr(cli, "GitHubClient", FakeClient)

    assert cli.main(["--repo", "example/project", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["repo"] == "example/project"
    assert payload["run"]["id"] == 123
