<div align="center">
  <h1>CI Queue Doctor</h1>
  <p><strong>Explain what GitHub Actions is waiting for—using evidence, not guesses.</strong></p>
  <p>
    <a href="https://github.com/cuijialin8888-code/ci-queue-doctor/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/cuijialin8888-code/ci-queue-doctor/actions/workflows/ci.yml/badge.svg"></a>
    <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
    <img alt="Runtime dependencies: zero" src="https://img.shields.io/badge/runtime%20dependencies-0-10b981">
    <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-0f172a"></a>
  </p>
  <p><a href="README.zh-CN.md">简体中文</a> · <a href="docs/safety.md">Safety boundary</a> · <a href="docs/triage.md">Triage guide</a> · <a href="#output-formats">Output formats</a></p>
</div>

GitHub Actions can remain `queued` without making the reason obvious. A run
may be waiting for a runner, a concurrency slot, an environment gate, or a
matrix dependency. CI Queue Doctor collects the public run/job payload and
turns the observable state into a small, auditable report.

It is deliberately conservative:

- **GET-only:** it never dispatches, reruns, cancels, approves, or edits a workflow.
- **Evidence-first:** every finding includes the fields that produced it.
- **Honest uncertainty:** it does not pretend to know GitHub's internal scheduler reason.
- **Zero runtime dependencies:** the CLI uses only the Python standard library.

## 30-second start

From a checkout:

```console
python -m ci_queue_doctor --repo OWNER/REPOSITORY
```

Inspect one run, use a five-minute threshold, and emit JSON:

```console
python -m ci_queue_doctor --repo OWNER/REPOSITORY --run 123456789 --threshold 5 --format json
```

Public repositories can usually be read without a token. For private
repositories or higher rate limits, provide a short-lived read token through
the environment rather than shell history:

```console
set GH_TOKEN=github_pat_...
python -m ci_queue_doctor --repo OWNER/REPOSITORY
```

PowerShell:

```powershell
$env:GH_TOKEN = "github_pat_..."
python -m ci_queue_doctor --repo OWNER/REPOSITORY
```

The token is sent only as an HTTPS `Authorization` header and is never part of
the report. Do not paste a token into an issue, log, or report artifact.

## Findings

Finding IDs are stable so a CI job or dashboard can act on them without
matching prose:

| ID | Meaning | Default level |
| --- | --- | --- |
| `CQD001` | Run exceeded the local queue threshold | warning |
| `CQD002` | Queued run has no visible job records yet | info |
| `CQD003` | Queued jobs are waiting for a runner | info/warning |
| `CQD004` | In-progress run still has queued jobs | info/warning |
| `CQD005` | A job is in GitHub's `waiting` state | info |
| `CQD010` | Run completed without a successful conclusion | warning |
| `CQD099` | Unknown status; classification is limited | warning |

The warning threshold is a local observation window, not a claim about
GitHub's internal scheduler. See [the safety boundary](docs/safety.md). For a repeatable interpretation workflow, see [the queue triage guide](docs/triage.md).

## Output formats

`--format text` is intended for a terminal. `json` is stable and suitable for
automation, `markdown` is convenient for a review comment, and `sarif` can be
uploaded to a code-scanning-compatible consumer.

Use `--fail-on warning` or `--fail-on error` when a monitoring job should fail
on a finding. The default is exit code 0 unless the API request itself fails.

## Development

```console
python -m venv .venv
.venv\Scripts\python -m pip install --index-url https://pypi.org/simple -e ".[dev]"
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check src tests
```

The project targets Python 3.10–3.13 and keeps the runtime package dependency
free. The development tools are intentionally optional.

## API references

- [List workflow runs](https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-repository)
- [Get a workflow run](https://docs.github.com/en/rest/actions/workflow-runs#get-a-workflow-run)
- [List jobs for a workflow run](https://docs.github.com/en/rest/actions/workflow-jobs#list-jobs-for-a-workflow-run)

## License

MIT. See [LICENSE](LICENSE).
