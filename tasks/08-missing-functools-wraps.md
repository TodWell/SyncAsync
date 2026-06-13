# Fix: missing functools.wraps on _sync_async_decorator

**File:** `SyncAsync/core.py:76`  
**Severity:** Low (cleanup)

## Problem

`_sync_async_decorator` is returned without `@functools.wraps(foo)`, so every
`@SyncAsync.sync`-decorated method loses its `__name__`, `__doc__`, `__qualname__`, and
`__annotations__`. `functools` is not imported in the file at all.

Concrete effects: `help(instance.method)` shows the wrapper's generic docstring; stack
traces display `_sync_async_decorator` instead of the real method name; `inspect.signature`
returns `(_self, *args, **kwargs)`; IDE autocompletion and type-checker inference are
broken for all decorated methods.

## Fix

```python
import functools

# inside sync():
@functools.wraps(foo)
def _sync_async_decorator(_self, *args, **kwargs) -> RetType:
    ...
```
