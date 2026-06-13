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
