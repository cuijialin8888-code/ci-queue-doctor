# Queue triage guide

CI Queue Doctor explains observable GitHub Actions run and job states. It does not know GitHub's private scheduler decisions and never changes a workflow.

Start with `python -m ci_queue_doctor --repo OWNER/REPOSITORY`. Inspect one run with `--run 123456789 --threshold 5 --format json` when the queue is ambiguous. The threshold is a local observation rule, not proof of an internal scheduler cause.

Read evidence in order: confirm status, conclusion, and timestamps; check whether public job records exist; separate queued, waiting, and in-progress jobs; record the stable `CQD###` ID and evidence fields; and use completion evidence once the run finishes.

For private repositories or higher rate limits, provide a short-lived token through `GH_TOKEN` or `GITHUB_TOKEN`, never in arguments, reports, issues, or logs. The client uses GET requests only: it never dispatches, reruns, cancels, approves, or edits workflows.