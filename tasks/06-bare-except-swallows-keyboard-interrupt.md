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
