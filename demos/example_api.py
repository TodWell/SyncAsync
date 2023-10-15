import asyncio
import random

from SyncAsync import SyncAsync


class ExampleTransaction(SyncAsync):

    async def execute(self):
        pass


class ExampleApi(SyncAsync):

    @SyncAsync.sync
    async def query_multiple(self, n=100):
        _results = []

        async def _query(idx: int):
            r = random.randint(0, 1000) / 1000
            await asyncio.sleep(r)
            _results.append((idx, r,))

        queries = [_query(ii) for ii in range(n)]
        await asyncio.gather(*queries)
        return _results

    def transaction(self, specifier="a"):
        return ExampleTransaction(parent=self)


async def aio_main():
    print("aio_main")
    api = ExampleApi()
    results = await api.query_multiple(20)
    print(results)


def main():
    print("main")
    api = ExampleApi()
    results = api.query_multiple(20)
    print(results)


if __name__ == "__main__":
    main()
    asyncio.get_event_loop().run_until_complete(aio_main())
