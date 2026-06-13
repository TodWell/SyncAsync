# Tests: real-world async HTTP with httpx

**File:** `tests/test_httpx.py` (new)  
**Severity:** Enhancement

## Goal

Validate that `SyncAsync` works correctly with a realistic async I/O client (`httpx`).
`httpx` is a natural fit: it ships an `AsyncClient` that must be used with `async with`
and `await`, making it a good stand-in for any async resource a user would wrap with
`@SyncAsync.sync`.

## Scenarios to cover

1. **Basic sync GET from sync context**  
   Subclass `SyncAsync`, wrap `httpx.AsyncClient.get` in a `@SyncAsync.sync` method,
   call it synchronously. Assert the response status and parsed JSON.

2. **Multiple sequential sync calls reuse the same loop**  
   Call the wrapped method twice on the same instance. Assert both succeed and that
   `obj._loop` is the same object both times (loop is not recreated per call).

3. **Sync call from a background thread**  
   Submit the sync call to a `ThreadPoolExecutor`. Assert the result is correct.
   (Regression guard for the `new_event_loop` fix in task 02.)

4. **Awaiting in async context**  
   Mark the test `@pytest.mark.asyncio` and `await` the same method. Assert the
   coroutine is returned directly and resolves correctly.

5. **Exception propagation over HTTP**  
   Point the client at an unreachable host or use `httpx.MockTransport` to return a
   non-2xx status; assert the exception or status propagates cleanly through the wrapper.

6. **Parent/child loop sharing with httpx**  
   Construct a parent `SyncAsync` and a child with `parent=self`. Both make async HTTP
   calls. Assert they share a single loop (`child._loop is None`, loop comes from parent).

## Notes

- Use `httpx.MockTransport` (or `respx` if available) so tests don't hit the network.
- Add `httpx` to the `[tool.poetry.dependencies]` test group if not already present.
- Session-scoped `AsyncClient` lifetime should be managed inside the `@SyncAsync.sync`
  method (open and close per call, or store on `self`) — pick whichever matches realistic
  usage and document the choice.
