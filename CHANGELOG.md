# Changelog

## [Unreleased]

- Add bounded, deterministic offline snapshot replay at the saved observation time; validate limits and finite thresholds before network access.
- Handle snapshots exceeding the JSON parser's nesting limit as input errors instead of uncaught recursion errors.

### Added

- A queue triage guide separating observable run states from GitHub scheduler claims.

## 0.1.0 — 2026-08-31

- Initial public release.
- Read-only GitHub Actions run and job inspection through GET requests.
- Evidence-backed queue classifications with stable `CQD###` finding IDs.
- Text, JSON, Markdown, and SARIF output.
- No runtime dependencies and no workflow execution or mutation.
