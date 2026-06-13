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

## Implementation

Chose the async test approach (no decorator on `recursive`) since adding `@SyncAsync.sync`
to a method that calls itself with `await self.recursive(...)` works but makes the intent
less clear — the method is designed to live in async contexts.

Also fixed a latent logic bug in `recursive` itself: the original condition
`if depth <= max_depth: return` with `depth=0, max_depth=100` caused immediate return
on every call, so no recursion ever occurred even when properly awaited. Fixed to
`if depth >= max_depth: return` with upward counting (`depth + 1`) and a small default
`max_depth=5` to keep tests fast.

## Lessons Learned

- A discarded coroutine (no `await`, no `asyncio.run`, no `loop.run_until_complete`)
  silently passes any assertion after it — always ensure async test code is actually
  executing by using `@pytest.mark.asyncio` + `await`.
- pytest-asyncio in STRICT mode (the default since 0.21) requires explicit
  `@pytest.mark.asyncio` on every async test; auto-mode is opt-in via `asyncio_mode = auto`
  in pytest config.
- Inverted base-case conditions (`<=` vs `>=`) in recursive async methods are easy to
  miss because a no-op coroutine still "passes" if never awaited.
