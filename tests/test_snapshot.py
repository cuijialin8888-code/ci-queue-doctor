import json

import pytest

from ci_queue_doctor import cli


def snapshot_data():
    return {
        "schemaVersion": 1,
        "repo": "example/project",
        "defaultBranch": "main",
        "capturedAt": "2026-08-31T12:20:00Z",
        "run": {"id": 123, "status": "queued", "created_at": "2026-08-31T12:00:00Z"},
        "jobs": [],
    }


def test_snapshot_is_offline_deterministic_and_keeps_gate(tmp_path, monkeypatch, capsys):
    def forbidden(**_kwargs):
        raise AssertionError("offline replay must not construct an API client")

    monkeypatch.setattr(cli, "GitHubClient", forbidden)
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_data()), encoding="utf-8")
    args = ["--snapshot", str(path), "--format", "json", "--fail-on", "warning"]
    before = path.read_bytes()
    assert cli.main(args) == 1
    first = capsys.readouterr().out
    assert cli.main(args) == 1
    assert capsys.readouterr().out == first
    assert json.loads(first)["repo"] == "example/project"
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("schemaVersion", 2),
        ("run", []),
        ("jobs", ["invalid"]),
        ("capturedAt", "2026-08-31"),
        ("repo", "../x"),
    ],
)
def test_malformed_snapshot_is_input_error(tmp_path, capsys, key, value):
    data = snapshot_data()
    data[key] = value
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert cli.main(["--snapshot", str(path)]) == 2
    assert "error:" in capsys.readouterr().err


def test_snapshot_cannot_select_a_live_run(tmp_path):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--snapshot", str(tmp_path / "x.json"), "--run", "123"])
    assert exc.value.code == 2


@pytest.mark.parametrize(("opening", "closing"), [("[", "]"), ('{"nested":', "}")])
def test_deeply_nested_snapshot_is_input_error(tmp_path, monkeypatch, capsys, opening, closing):
    def forbidden(**_kwargs):
        raise AssertionError("invalid snapshot must not construct an API client")

    monkeypatch.setattr(cli, "GitHubClient", forbidden)
    # JSON decoder nesting limits differ from Python's recursion limit across versions.
    depth = 20_000
    raw = json.dumps(snapshot_data())[:-1] + ', "extra": '
    raw += opening * depth + "0" + closing * depth + "}"
    path = tmp_path / "nested.json"
    path.write_text(raw, encoding="utf-8")
    before = path.read_bytes()
    assert cli.main(["--snapshot", str(path)]) == 2
    captured = capsys.readouterr()
    assert "nesting" in captured.err
    assert captured.out == ""
    assert path.read_bytes() == before


@pytest.mark.parametrize("value", ["nan", "inf", "-1"])
def test_nonfinite_threshold_is_rejected_before_network(value, monkeypatch, capsys):
    def forbidden(**_kwargs):
        raise AssertionError("invalid input must not access the network")

    monkeypatch.setattr(cli, "GitHubClient", forbidden)
    assert cli.main(["--repo", "example/project", "--threshold", value]) == 2
    assert "error:" in capsys.readouterr().err
