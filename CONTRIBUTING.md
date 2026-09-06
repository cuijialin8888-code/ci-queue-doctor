# Contributing

Thanks for helping improve CI Queue Doctor. Keep changes small, evidence-backed, and compatible with the tool's safety boundary.

## Runtime and safety boundary

- Keep the CLI GET-only: it must never dispatch, rerun, cancel, approve, or edit a GitHub Actions workflow.
- Keep runtime dependencies at zero and do not add telemetry.
- Do not include `GH_TOKEN` values, authorization headers, private repository URLs, or unredacted job output in issues, fixtures, or reports.

## Local verification

From a checkout, use the documented development checks before submitting a behavioral change:

```console
python -m pytest -q
python -m ruff check src tests
```

Treat a queued or inaccessible API response as evidence-limited. The tool must not claim knowledge of GitHub's internal scheduler.

## Pull requests

- Add focused tests for every changed finding or output field.
- Keep finding IDs and JSON/SARIF fields stable unless the change is explicitly documented.
- Update the English and Chinese README files when command behavior or safety boundaries change.
- Wait for public CI to complete successfully before treating a change as accepted.
