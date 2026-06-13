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

## Implementation

- Added `import functools` at the top of `SyncAsync/core.py`.
- Applied `@functools.wraps(foo)` to `_sync_async_decorator` and removed its now-redundant
  generic docstring (the wrapper inherits `__doc__` from `foo`).

## Lessons Learned

- `@functools.wraps(foo)` copies `__name__`, `__qualname__`, `__doc__`, `__annotations__`,
  and `__wrapped__` from the wrapped function; `inspect.signature` follows `__wrapped__` to
  show the original parameter list.
- Tests for `__name__` and `__qualname__` should assert on the **class attribute**
  (e.g. `TestClass.a.__name__`) rather than an instance attribute, because `@staticmethod`
  and descriptor protocol mean the attribute is accessible on the class directly.
- The generic wrapper docstring should be removed when `@functools.wraps` is added —
  otherwise `foo.__doc__ = None` leaves no documentation at all, and the wrapper's old
  docstring is lost anyway.
