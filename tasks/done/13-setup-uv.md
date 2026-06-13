# Task 13: Migrate from Poetry to uv

Migrate the project from Poetry to [uv](https://docs.astral.sh/uv/) and support running tests on Python 3.11–3.14.

## What changed

- `pyproject.toml` rewritten to PEP 621 format (`[project]` table, hatchling build backend).
  - Runtime dependency `nest-asyncio>=1.5` moved to `[project.dependencies]` (was implicit before).
  - Test dependencies (`pytest`, `pytest-asyncio`, `httpx`) in `[project.optional-dependencies] test`.
- `uv.lock` now committed (replaces `poetry.lock`).
- `poetry.lock` deleted; removed from `.gitignore`.
- `tox.ini` added: `envlist = py311, py312, py313, py314` with `skip_missing_interpreters = true`.
- `CLAUDE.md` updated with `uv run` / `tox` commands.

## Key commands

```bash
uv sync --extra test        # install into .venv
uv run --extra test pytest  # run tests
tox                         # run across all Python versions
```

## Lessons learned

- `uv run --extra <group>` is the uv equivalent of `poetry run` with an extras group; use `uv sync --extra <group>` to populate `.venv` first.
- `nest-asyncio` was already a hidden runtime dep (imported inside `loop` property); PEP 621 makes this explicit in `[project.dependencies]`.
- `hatchling` needs `[tool.hatch.build.targets.wheel] packages = ["SyncAsync"]` when the package directory name differs from the distribution name or uses a capital letter.
- tox's `skip_missing_interpreters = true` is essential so CI/local runs don't fail if not all Python versions are installed.
- `poetry.lock` was in `.gitignore`; remove that entry when removing Poetry so the ignore file stays clean.
- A hook bumped the version to 0.2.0 on `uv lock`; reverted to 0.1.0 since this was a tooling migration, not a version release.
