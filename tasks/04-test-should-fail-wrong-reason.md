# Fix: test_should_fail passes for the wrong reason

**File:** `tests/test_basics.py:91`  
**Severity:** Medium

## Problem

`test_should_fail` is an async test, so the pytest-asyncio event loop is running. When
`d()` calls `self.a()`, the `is_running()` branch fires and returns a raw coroutine
instead of `0`. `d()` then evaluates `coroutine + 0`, which raises `TypeError` — not the
reentrancy or deadlock the test name implies. The test catches `Exception` and passes, but
the coroutine is never awaited and Python emits `RuntimeWarning: coroutine 'TestClass.a'
was never awaited`.

## Fix

Clarify the intended failure scenario and test it explicitly. If the intent is to verify
that calling a sync-wrapping method from inside a running async context returns a
coroutine (not a value), assert that directly:

```python
@pytest.mark.asyncio
async def test_sync_method_inside_async_returns_coroutine(simple_class):
    import inspect
    result = simple_class.a()   # loop is running — returns coroutine
    assert inspect.iscoroutine(result)
    await result                # consume it to avoid RuntimeWarning
```
