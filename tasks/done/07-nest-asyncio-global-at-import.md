# Fix: nest_asyncio.apply() called globally at import time

**File:** `SyncAsync/core.py:43`  
**Severity:** Medium

## Problem

`nest_asyncio.apply()` is called unconditionally at module import time for all
Jupyter/Spyder users. This mutates the running event loop for the entire process, not just
for `SyncAsync` instances. Other libraries in the same kernel that rely on non-reentrant
loop semantics can break in ways that are hard to diagnose.

## Fix

Move the `nest_asyncio` patch into the `SyncAsync.__init__` or `loop` property so it is
applied only when a `SyncAsync` instance is actually constructed, and ideally only per-
loop rather than globally. At minimum, document clearly that importing `SyncAsync` in a
Jupyter/Spyder environment patches the global event loop.

## Implementation

Moved the `nest_asyncio.apply()` call from module-level into the `loop` property
(`SyncAsync/core.py`). It is now called only when a new loop is created
(`self._loop is None`) and receives the specific loop as its argument:

```python
nest_asyncio.apply(self._loop)
```

This ensures:
- No side-effects on import.
- Only the loop owned by this `SyncAsync` instance is patched, not any ambient loop.
- The patch is applied exactly once per loop instance (the guard `if self._loop is None`
  prevents re-entry on subsequent `.loop` accesses).

## Lessons Learned

- `nest_asyncio` is **not** listed in `pyproject.toml` dependencies; it is an optional
  runtime dependency expected to be present only in Jupyter/Spyder environments. Tests must
  mock it via `sys.modules` rather than importing it directly.
- `monkeypatch.setitem(sys.modules, "nest_asyncio", mock)` is the right idiom to inject a
  fake module for an `import` that happens inside library code under test.
- `nest_asyncio.apply(loop)` accepts the loop as a positional-or-keyword argument; passing
  it explicitly scopes the patch to that loop rather than the process-wide current loop.
