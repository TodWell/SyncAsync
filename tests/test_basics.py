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
