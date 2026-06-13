# Cleanup: unused `List` import from typing

**File:** `SyncAsync/core.py:5`  
**Severity:** Low (cleanup)

## Problem

`List` is imported from `typing` on line 5 but never referenced anywhere in the file.
On Python 3.9+ the built-in `list` can be used directly in annotations, making this
import doubly unnecessary. Linters (Flake8 F401, Ruff) flag it as an error.

## Fix

Remove `List` from the import:

```python
from typing import Callable, Awaitable, ParamSpec, TypeVar, Concatenate, Union
```
