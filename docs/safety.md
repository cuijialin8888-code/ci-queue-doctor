# Safety and evidence boundary

`ci-queue-doctor` answers a narrow question: what queue-related state is
observable from the GitHub REST API at this moment?

It does not claim to know GitHub's internal scheduler decision. A warning such
as `CQD001` means that the observed run exceeded the local threshold; it is not
proof that GitHub is broken. The next-step text points to runner capacity,
concurrency, environment gates, and the Actions UI because those causes cannot
be distinguished from the public run/job payload alone.

The command performs only these reads:

1. Repository metadata, to identify the default branch.
2. The latest matching workflow run, or one explicit run ID.
3. Jobs for that run.

No checkout is performed. No workflow, shell command, job, issue, pull
request, repository setting, or credential is changed.
