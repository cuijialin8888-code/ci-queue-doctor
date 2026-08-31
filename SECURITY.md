# Security policy

## Scope

`ci-queue-doctor` is intentionally read-only. It requests GitHub REST API
resources with `GET` only and does not dispatch, rerun, cancel, approve, or
modify workflows.

The tool never prints the value of `GH_TOKEN` or `GITHUB_TOKEN`. Prefer a
short-lived token with the smallest read scope needed for the target
repository. Public repositories can usually be inspected without a token.

## Reporting a vulnerability

Please use GitHub's private security advisory flow for this repository rather
than publishing credentials or an exploit in an issue. If private reporting is
not available, open a minimal issue without secrets and request a maintainer
contact channel.
