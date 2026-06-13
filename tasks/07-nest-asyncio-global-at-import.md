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
