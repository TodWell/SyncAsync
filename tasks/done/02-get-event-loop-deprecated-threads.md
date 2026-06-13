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

**Coupled fix required:** Changing to `new_event_loop()` means the instance's loop is
never the ambient running loop, so the old `_self.loop.is_running()` check in
`_sync_async_decorator` always returns `False` inside an async context (e.g.
pytest-asyncio). Replace it with `asyncio.get_running_loop()` (raises `RuntimeError`
if no loop is running) to detect the ambient loop independently of the instance's owned
loop:

```python
try:
    asyncio.get_running_loop()
    ambient_loop_running = True
except RuntimeError:
    ambient_loop_running = False

if ambient_loop_running:
    return foo(_self, *args, **kwargs)
```

## Learned Lessons

- `new_event_loop()` and `get_event_loop()` are not drop-in substitutes when the code
  also relies on `loop.is_running()` to detect an async context. The two changes must
  be made together: own the loop explicitly with `new_event_loop()`, and detect the
  ambient running loop with `asyncio.get_running_loop()`.
- `asyncio.get_running_loop()` (3.7+) is the correct, non-deprecated way to ask "is
  there currently a running event loop?" — it raises `RuntimeError` rather than
  silently returning a stale or thread-local loop.
- A thread test using `concurrent.futures.ThreadPoolExecutor` is the minimal regression
  guard for this class of bug; add one whenever `asyncio.get_event_loop()` is replaced.
