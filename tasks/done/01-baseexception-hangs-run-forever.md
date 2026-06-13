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

## Learned lessons

- The `finally` block also lets us delete the standalone `_self.loop.stop()` call that
  previously sat after the `else` block, eliminating the duplicate call path.
- `KeyboardInterrupt` and `SystemExit` are straightforward to test: raise them inside a
  `@SyncAsync.sync` method and assert `pytest.raises` catches them from the sync call site.
- `GeneratorExit` was intentionally left out of the test suite — it is only raised by
  the interpreter when a generator/coroutine is garbage-collected or explicitly closed,
  so constructing a deterministic unit test for it inside `_runnable` is not practical.
  The `finally` guarantee covers it implicitly.
- The pre-existing `DeprecationWarning` (`asyncio.get_event_loop()` with no running loop)
  is unrelated to this fix and tracked separately.
