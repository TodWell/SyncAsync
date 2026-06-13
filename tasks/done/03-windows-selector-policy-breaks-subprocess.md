# Fix: WindowsSelectorEventLoopPolicy set globally breaks subprocess support

**File:** `SyncAsync/core.py:51`  
**Severity:** High

## Problem

`asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())` is applied at
import time for all Windows users. `SelectorEventLoop` does not support
`asyncio.create_subprocess_exec` or `asyncio.create_subprocess_shell` on Windows — those
require `ProactorEventLoop` (the Python 3.8+ default). Any application that imports
`SyncAsync` and later uses async subprocesses will get `NotImplementedError`, regardless
of what policy it set before importing.

## Fix

Scope this to only the environments that need it (Spyder), or document the limitation
clearly and let users opt out:

```python
# Only apply when running inside Spyder, where ProactorEventLoop causes issues
if is_spyder() and os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

Alternatively, move the policy change into `__init__` behind an explicit flag so callers
can disable it.

## Implementation

Applied the first option — scoped `WindowsSelectorEventLoopPolicy` to `is_spyder() and os.name == "nt"` in `core.py`.

## Tests Added (`tests/test_basics.py`)

- `test_windows_selector_policy_not_forced_globally` — asserts the active policy is not `WindowsSelectorEventLoopPolicy` on non-Spyder Windows after import.
- `test_subprocess_works_after_import` — creates a real subprocess via `asyncio.create_subprocess_exec` inside a `@SyncAsync.sync` method; this would raise `NotImplementedError` on Windows with the old global `SelectorEventLoop` policy.

## Lessons Learned

- Libraries must never unconditionally mutate global process state (event loop policy, signal handlers, etc.) at import time; scope any such change to the narrowest environment that actually requires it.
- The Python 3.8+ default on Windows is `ProactorEventLoop`, which supports subprocesses — `SelectorEventLoop` was only needed as a workaround for Spyder's internal asyncio usage.
- Regression tests should exercise the concrete capability that was broken (subprocess creation), not just assert on policy type, so the test is meaningful on all platforms.
