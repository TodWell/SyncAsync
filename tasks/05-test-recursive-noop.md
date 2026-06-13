# Fix: test_asynchronous_recursive is a no-op

**File:** `tests/test_basics.py:74`  
**Severity:** Medium

## Problem

`recursive` is an `async def` method with no `@SyncAsync.sync` decorator. Calling
`simple_class.recursive()` from synchronous test code creates a coroutine object and
immediately discards it — nothing executes. The test always passes and provides zero
coverage of the recursive logic. Python emits `RuntimeWarning: coroutine
'TestClass.recursive' was never awaited`.

## Fix

Either decorate `recursive` with `@SyncAsync.sync` so it can be called synchronously,
or await it inside an async test:

```python
@pytest.mark.asyncio
async def test_asynchronous_recursive(simple_class):
    await simple_class.recursive()  # actually runs the coroutine
    assert True
```
