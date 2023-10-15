# SyncAsync

This library enables you to provide your asynchronous library to synchronous users,
while still enabling you, to use it as intended.

## Installation
```commandline
pip install sync-async
```

## Hello World
```python
from SyncAsync import SyncAsync

class Example(SyncAsync):

    @SyncAsync.sync
    async def hello_world(self, txt: str):
        print(txt)


        
def main(api: Example):  
    api.hello_world("Hello World")  


async def aio_main(api: Example):
    await api.hello_world("Hello Sky")

if __name__ == "__main__":
    example = Example()
    main(example)  # Prints 'Hello World'
    import asyncio
    asyncio.get_event_loop().run_until_complete(aio_main(example))  # Prints 'Hello Sky'
```