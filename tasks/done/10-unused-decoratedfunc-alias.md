# Cleanup: unused and misleading DecoratedFunc type alias

**File:** `SyncAsync/core.py:59`  
**Severity:** Low (cleanup)

## Problem

`DecoratedFunc = Callable[Concatenate[str, Param], RetType]` is defined but never used.
Worse, `Concatenate[str, Param]` implies the decorator prepends a `str` argument, which
is factually wrong — it prepends `_self`. If a contributor uses this alias to annotate
`sync`'s return type it will introduce a type error.

## Fix

Delete the alias:

```python
# remove this line:
DecoratedFunc = Callable[Concatenate[str, Param], RetType]
```

And remove `Concatenate` from the `typing` import if it is not used elsewhere.
