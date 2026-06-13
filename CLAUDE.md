# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`SyncAsync` is a small Python library that lets async methods on a class be called synchronously — without the caller needing to know they're async. It is managed with [uv](https://docs.astral.sh/uv/) and targets Python 3.11–3.14.

## Commands

```bash
# Install dependencies (including test extras)
uv sync --extra test

# Run all tests
uv run --extra test pytest

# Run a single test
uv run --extra test pytest tests/test_basics.py::test_asynchronous_method

# Run tests across all supported Python versions (requires py3.11–py3.14 on PATH)
tox

# Run the demo
uv run python demos/example_api.py
```

## Architecture

All library code lives in `SyncAsync/core.py`. The public API is re-exported from `SyncAsync/__init__.py`.

### How `@SyncAsync.sync` works

`SyncAsync` is an abstract base class. Subclasses decorate `async` methods with `@SyncAsync.sync`. The decorator returns a wrapper that inspects the event loop at call time:

- **Loop already running** (async context / Jupyter / Spyder): returns the coroutine directly so it can be `await`ed normally.
- **Loop not running** (sync context): spins up `loop.run_forever()`, schedules the coroutine via `asyncio.ensure_future`, captures the result or re-raises any exception, then stops the loop and returns synchronously.

This dual behaviour is what makes the same method callable both ways without branching in user code.

### `loop` property and parent chaining

Each `SyncAsync` instance owns or inherits an event loop. Passing `parent=self` when constructing a child object (e.g. `ChildClass(parent=self)`) makes the child share the parent's loop. This is important: mixing loops between parent and child objects will break sync-from-sync calls.

### Environment detection

On module import, `core.py` detects Jupyter (`IPKernelApp` in IPython config) and Spyder (`SPY_PYTHONPATH` env var). In either environment it applies `nest_asyncio` so that `loop.run_forever()` can be called inside an already-running loop. On Windows it sets `WindowsSelectorEventLoopPolicy` to avoid `NotImplementedError` from `ProactorEventLoop`.

### Key invariant

A `@SyncAsync.sync` method **must** be `async def`. The wrapper always `await`s it internally when running the loop itself; when the loop is already running it hands back the coroutine to the caller. Decorating a plain `def` will break silently.
