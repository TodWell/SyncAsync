# Fix: bare except: in is_notebook() swallows KeyboardInterrupt

**File:** `SyncAsync/core.py:28,33`  
**Severity:** Medium

## Problem

Both `except:` blocks in `is_notebook()` catch `BaseException`, which includes
`KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`. A Ctrl-C pressed while the module
is being imported (during `get_ipython()` or `.config` access) is silently swallowed and
the function returns `False`, leaving the process running when the user intended to abort.

## Fix

Replace bare `except:` with `except Exception:`, or name the specific exceptions expected
at each site:

```python
def is_notebook():
    try:
        from IPython import get_ipython
    except ImportError:
        return False
    try:
        if "IPKernelApp" not in get_ipython().config:
            raise ImportError("console")
    except Exception:
        return False
    else:
        return True
```

## Implementation

Applied exactly as specified. Two tests were added to `tests/test_basics.py`:

1. `test_is_notebook_returns_false_without_ipython` — patches `sys.modules["IPython"]` to `None`
   so the `except ImportError:` path is exercised and the function returns `False`.
2. `test_is_notebook_does_not_swallow_keyboard_interrupt` — patches a mock IPython whose
   `get_ipython` raises `KeyboardInterrupt`; verifies it propagates instead of being caught.

## Lessons Learned

- Bare `except:` in Python catches `BaseException`, not just `Exception` — that silently
  swallows `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`. Always be explicit:
  use `except ImportError:` when you only expect import failures, or `except Exception:`
  when you want a broad catch but still let signals through.
- `patch.dict("sys.modules", {"IPython": None})` reliably triggers `ImportError` for
  `from IPython import ...`, making it a clean unit-test shim for optional imports.
- Functions called at module-import time (like `is_notebook()`) are still callable in
  tests — mock at the `sys.modules` level to control the environment they see.
