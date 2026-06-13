# Fix: asyncio.get_event_loop() broken in threads on Python 3.10+

**File:** `SyncAsync/core.py:125`  
**Severity:** High

## Problem

`asyncio.get_event_loop()` emits `DeprecationWarning` on Python 3.10+ when no current
loop exists, and raises `RuntimeError` in non-main threads on Python 3.12+. The library
requires Python ≥3.11, so every `SyncAsync` instance used inside a `ThreadPoolExecutor`
or background thread will crash on the first `.loop` access.

## Fix

Replace `asyncio.get_event_loop()` with `asyncio.new_event_loop()` to make ownership
explicit:

```python
@property
def loop(self):
    if self._parent:
        return self._parent.loop
    if self._loop is None:
        self._loop = asyncio.new_event_loop()
    return self._loop
```

Note: if sharing the ambient main-thread loop is intentional, wrap with
`try/except RuntimeError` and fall back to `asyncio.new_event_loop()`.
