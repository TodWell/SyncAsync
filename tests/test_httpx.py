import concurrent.futures

import httpx
import pytest

from SyncAsync import SyncAsync


def _mock_transport(status=200, json_body=None):
    body = json_body if json_body is not None else {"hello": "world"}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler)


class ApiService(SyncAsync):
    """Wraps httpx.AsyncClient with @SyncAsync.sync, opening/closing the client per call."""

    def __init__(self, transport=None, **kwargs):
        super().__init__(**kwargs)
        self._transport = transport or _mock_transport()

    @SyncAsync.sync
    async def get(self, url="https://example.com") -> httpx.Response:
        async with httpx.AsyncClient(transport=self._transport) as client:
            return await client.get(url)

    def child_service(self):
        return ApiService(parent=self, transport=self._transport)


# --- Scenario 1: basic sync GET ---

def test_sync_get_status_and_json():
    client = ApiService()
    resp = client.get()
    assert resp.status_code == 200
    assert resp.json() == {"hello": "world"}


# --- Scenario 2: multiple sequential calls reuse same loop ---

def test_sequential_calls_reuse_loop():
    client = ApiService()
    client.get()
    loop_after_first = client._loop
    client.get()
    assert client._loop is loop_after_first


# --- Scenario 3: sync call from background thread ---

def test_sync_call_from_thread():
    def task():
        return ApiService().get()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        resp = pool.submit(task).result()
    assert resp.status_code == 200


# --- Scenario 4: awaiting in async context ---

@pytest.mark.asyncio
async def test_await_in_async_context():
    client = ApiService()
    resp = await client.get()
    assert resp.status_code == 200
    assert resp.json() == {"hello": "world"}


# --- Scenario 5: exception propagation ---

def test_connect_error_propagates():
    def error_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unreachable")

    client = ApiService(transport=httpx.MockTransport(error_handler))
    with pytest.raises(httpx.ConnectError):
        client.get()


def test_http_error_status_propagates():
    client = ApiService(transport=_mock_transport(status=404))
    resp = client.get()
    assert resp.status_code == 404
    with pytest.raises(httpx.HTTPStatusError):
        resp.raise_for_status()


# --- Scenario 6: parent/child loop sharing ---

def test_parent_child_share_loop():
    parent = ApiService()
    child = parent.child_service()

    parent_resp = parent.get()
    child_resp = child.get()

    assert parent_resp.status_code == 200
    assert child_resp.status_code == 200
    assert child._loop is None
    assert child.loop is parent.loop
