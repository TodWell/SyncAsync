import asyncio
import sys

import pytest

from SyncAsync import SyncAsync


class ChildClass(SyncAsync):

    @SyncAsync.sync
    async def child_a(self):
        return 0


class TestClass(SyncAsync):

    @SyncAsync.sync
    async def a(self):
        return 0

    def b(self):
        return 0

    @SyncAsync.sync
    async def c(self):
        a = await self.a()
        b = self.b()
        return a + b

    def d(self):
        a = self.a()
        b = self.b()
        return a + b

    def hinting(self, x: int, y=2):
        return x - y

    @SyncAsync.sync
    async def aio_hinting(self, x: int, y=2):
        return x - y

    @SyncAsync.sync
    async def aio_raise_exception(self):
        raise KeyError("key error")

    @SyncAsync.sync
    async def aio_raise_keyboard_interrupt(self):
        raise KeyboardInterrupt()

    @SyncAsync.sync
    async def aio_raise_system_exit(self):
        raise SystemExit(1)

    def child(self):
        return ChildClass(parent=self)

    async def recursive(self, depth=0, max_depth=5):
        if depth >= max_depth:
            return
        await self.recursive(depth + 1, max_depth)


@pytest.fixture
def simple_class():
    return TestClass()


def test_synchronous_method(simple_class: TestClass):
    assert simple_class.b() == 0


def test_asynchronous_method(simple_class: TestClass):
    assert simple_class.a() == 0


def test_asynchronous_method_calling_asynchronous(simple_class: TestClass):
    assert simple_class.c() == 0


def test_asynchronous_method_calling_synchronous(simple_class: TestClass):
    assert simple_class.d() == 0

@pytest.mark.asyncio
async def test_asynchronous_recursive(simple_class: TestClass):
    await simple_class.recursive()


@pytest.mark.asyncio
async def test_aio_simple(simple_class: TestClass):
    a = await simple_class.a()
    assert a == 0
    b = simple_class.b()
    assert b == 0
    c = await simple_class.c()
    assert c == 0


@pytest.mark.asyncio
async def test_sync_method_inside_async_returns_coroutine(simple_class: TestClass):
    """When the event loop is already running, @SyncAsync.sync returns the raw coroutine."""
    import inspect
    result = simple_class.a()  # loop is running — returns coroutine, not 0
    assert inspect.iscoroutine(result)
    await result  # consume to avoid RuntimeWarning


def test_hinting(simple_class: TestClass):
    assert simple_class.hinting(2) == 0
    assert simple_class.aio_hinting(2) == 0


@pytest.mark.asyncio
async def test_aio_hinting(simple_class: TestClass):
    a = await simple_class.aio_hinting(2)
    assert a == 0
    b = simple_class.hinting(2)
    assert b == 0


def test_key_error(simple_class: TestClass):
    try:
        simple_class.aio_raise_exception()
    except KeyError:
        assert True
    else:
        assert False


def test_child(simple_class: TestClass):
    child = simple_class.child()
    assert child.child_a() == 0
    assert simple_class.a() == 0


def test_keyboard_interrupt_propagates(simple_class: TestClass):
    with pytest.raises(KeyboardInterrupt):
        simple_class.aio_raise_keyboard_interrupt()


def test_system_exit_propagates(simple_class: TestClass):
    with pytest.raises(SystemExit):
        simple_class.aio_raise_system_exit()


def test_sync_in_thread():
    """SyncAsync must work from a background thread (no ambient event loop)."""
    import concurrent.futures

    def thread_task():
        obj = TestClass()
        return obj.a()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(thread_task)
        assert future.result() == 0


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only policy check")
def test_windows_selector_policy_not_forced_globally():
    """Importing SyncAsync must not force WindowsSelectorEventLoopPolicy on non-Spyder Windows."""
    import os
    if "SPY_PYTHONPATH" not in os.environ:
        policy = asyncio.get_event_loop_policy()
        assert not isinstance(policy, asyncio.WindowsSelectorEventLoopPolicy)


class SubprocessClass(SyncAsync):
    @SyncAsync.sync
    async def echo(self):
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", "print('ok')",
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.strip()


def test_subprocess_works_after_import():
    """asyncio.create_subprocess_exec must not raise NotImplementedError after importing SyncAsync."""
    obj = SubprocessClass()
    result = obj.echo()
    assert result == b"ok"


def test_is_notebook_returns_false_without_ipython():
    from unittest.mock import patch
    from SyncAsync.core import is_notebook
    with patch.dict("sys.modules", {"IPython": None}):
        assert is_notebook() is False


def test_nest_asyncio_applied_per_loop_in_spyder(monkeypatch):
    """In a simulated Spyder env, nest_asyncio.apply() must receive the instance loop, not None."""
    import sys
    import SyncAsync.core as core
    from unittest.mock import MagicMock

    applied_with = []
    mock_nest = MagicMock()
    mock_nest.apply.side_effect = lambda loop=None: applied_with.append(loop)

    monkeypatch.setattr(core, "is_spyder", lambda: True)
    monkeypatch.setattr(core, "is_notebook", lambda: False)
    monkeypatch.setitem(sys.modules, "nest_asyncio", mock_nest)
    obj = TestClass()
    loop = obj.loop
    assert len(applied_with) == 1
    assert applied_with[0] is loop


def test_nest_asyncio_not_applied_in_normal_env(monkeypatch):
    """In a normal (non-Spyder, non-Jupyter) env, nest_asyncio.apply() must not be called."""
    import sys
    import SyncAsync.core as core
    from unittest.mock import MagicMock

    mock_nest = MagicMock()

    monkeypatch.setattr(core, "is_spyder", lambda: False)
    monkeypatch.setattr(core, "is_notebook", lambda: False)
    monkeypatch.setitem(sys.modules, "nest_asyncio", mock_nest)
    obj = TestClass()
    _ = obj.loop
    mock_nest.apply.assert_not_called()


def test_nest_asyncio_applied_only_once_per_loop(monkeypatch):
    """Accessing .loop multiple times must only apply nest_asyncio once."""
    import sys
    import SyncAsync.core as core
    from unittest.mock import MagicMock

    call_count = [0]
    mock_nest = MagicMock()
    mock_nest.apply.side_effect = lambda loop=None: call_count.__setitem__(0, call_count[0] + 1)

    monkeypatch.setattr(core, "is_spyder", lambda: True)
    monkeypatch.setattr(core, "is_notebook", lambda: False)
    monkeypatch.setitem(sys.modules, "nest_asyncio", mock_nest)
    obj = TestClass()
    _ = obj.loop
    _ = obj.loop
    _ = obj.loop
    assert call_count[0] == 1


def test_is_notebook_does_not_swallow_keyboard_interrupt():
    """is_notebook() must let KeyboardInterrupt propagate (bare except: used to swallow it)."""
    from unittest.mock import patch, MagicMock
    from SyncAsync.core import is_notebook

    mock_ipython = MagicMock()
    mock_ipython.get_ipython.side_effect = KeyboardInterrupt

    with patch.dict("sys.modules", {"IPython": mock_ipython}):
        with pytest.raises(KeyboardInterrupt):
            is_notebook()
