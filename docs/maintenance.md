# Maintainer checklist

The project is intentionally small and dependency-free at runtime.

## Before a release

1. Run `python -m pytest -q` and `python -m ruff check src tests`.
2. Run `python -m compileall -q src tests`.
3. Build both wheel and sdist with `python -m build --outdir dist`.
4. Install the wheel into a fresh virtual environment and run `ci-queue-doctor --help`.
5. Inspect the package file list and ensure no token, local path, or temporary file is included.
6. Review the public GitHub Actions result on the exact release commit.

## Before changing API behavior

- Keep the REST client GET-only.
- Add a fixture-backed test for every new observable status.
- Keep stable `CQD###` IDs; document any new ID in both READMEs.
- State what the API cannot prove instead of inferring an internal GitHub cause.
