# Task 12: Type Hints in Sync Code (PyCharm)

## Was this solved by task 08?

Partially. Task 08 added `@functools.wraps(foo)`, which fixed the **runtime** side:
`__name__`, `__qualname__`, `__doc__`, `__annotations__`, and `__wrapped__` are all copied
from the original async function. `inspect.signature` follows `__wrapped__` and returns the
original parameter list including annotations.

The **static** side was still broken: the type signature of `sync()` itself was wrong, so
PyCharm's type checker could not infer parameter types or return types for decorated methods.

## Root Cause

The original `sync()` signature:

```python
def sync(foo: OriginalFunction) -> Union[RetType, Callable[[ParamSpec], Awaitable[RetType]]]:
```

has multiple problems:
1. `OriginalFunction = Callable[Param, RetType]` does not constrain to async functions
   (no `Awaitable[RetType]` requirement)
2. The return type uses free TypeVars (`RetType`, `ParamSpec`) that are not bound to anything
   in the input — a type error
3. `Callable[[ParamSpec], ...]` uses the `ParamSpec` class itself (not an instance), which is
   meaningless as a callable argument list

## Fix

`SyncAsync/core.py` — replace `Param`/`RetType`/`OriginalFunction` with proper `P`/`T` and
rewrite the signature using `Concatenate` to thread `self` through:

```python
P = ParamSpec("P")
T = TypeVar("T")

@staticmethod
def sync(
    foo: Callable[Concatenate[Any, P], Awaitable[T]]
) -> Callable[Concatenate[Any, P], Union[T, Awaitable[T]]]:
```

Now when PyCharm sees `@SyncAsync.sync` applied to `async def aio_hinting(self, x: int, y: int = 2) -> int`,
it correctly binds `P` to `(x: int, y: int = 2)` and `T` to `int`, giving the decorated
method the type `(x: int, y: int = 2) -> int | Awaitable[int]`.

## Implementation

- `SyncAsync/core.py`: Added `Any` to typing imports; replaced `Param`, `RetType`,
  `OriginalFunction` with `P = ParamSpec("P")` and `T = TypeVar("T")`; fixed `sync()`
  return type signature; updated `_sync_async_decorator` inner annotation to
  `Union[T, Awaitable[T]]`.
- `tests/test_basics.py`: Added full annotations to `aio_hinting` (`y: int`, `-> int`);
  added `test_type_hints_preserved_in_annotations` (via `typing.get_type_hints`) and
  `test_sync_decorator_preserves_return_annotation` (via `inspect.signature`).

## Lessons Learned

- `functools.wraps` solves the **runtime** metadata problem (`inspect.signature`,
  `typing.get_type_hints`, `__name__`, etc.) but does nothing for static type checkers.
- For a decorator that wraps `async def` methods, use
  `Callable[Concatenate[Any, P], Awaitable[T]]` as the input type and
  `Callable[Concatenate[Any, P], Union[T, Awaitable[T]]]` as the return type.
  `Concatenate[Any, P]` accounts for the `self` parameter without needing to know its type.
- The return type `Union[T, Awaitable[T]]` is accurate: at runtime the method returns `T`
  in sync context and `Awaitable[T]` in async context. Type narrowing is the caller's
  responsibility — the library cannot encode the ambient loop state in the type system.
- `typing.get_type_hints()` reads `__annotations__` directly (set by `functools.wraps`);
  `inspect.signature()` follows `__wrapped__`. Both are useful to test, but they exercise
  different paths.
