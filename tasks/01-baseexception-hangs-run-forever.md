# Fix: BaseException in decorated method hangs run_forever()

**File:** `SyncAsync/core.py:96`  
**Severity:** Critical

## Problem

`_runnable()` only catches `Exception`, not `BaseException`. If the decorated async
method raises `KeyboardInterrupt`, `SystemExit`, or `GeneratorExit`, the exception
escapes the `except` block, `loop.stop()` is never called, and `run_forever()` blocks
indefinitely — making the process unresponsive.

## Fix

Change `except Exception` to `except BaseException` and move `loop.stop()` into a
`finally` block so it always fires:

```python
async def _runnable():
    try:
        foo_result = await foo(_self, *args, **kwargs)
    except BaseException as ex:
        res[:] = ex, False
    else:
        res[:] = foo_result, True
    finally:
        _self.loop.stop()
```
