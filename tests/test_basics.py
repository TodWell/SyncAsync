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

    def child(self):
        return ChildClass(parent=self)

    async def recursive(self, depth=0, max_depth = 100):
        if depth <= max_depth:
            return
        await self.recursive(depth - 1, max_depth)


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

def test_asynchronous_recursive(simple_class: TestClass):
    simple_class.recursive()
    assert True


@pytest.mark.asyncio
async def test_aio_simple(simple_class: TestClass):
    a = await simple_class.a()
    assert a == 0
    b = simple_class.b()
    assert b == 0
    c = await simple_class.c()
    assert c == 0


@pytest.mark.asyncio
async def test_should_fail(simple_class: TestClass):
    try:
        d = simple_class.d()
    except Exception as ex:
        assert True
    else:
        assert False


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
