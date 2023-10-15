import abc
import asyncio

import logging
from typing import Callable, Awaitable, ParamSpec, TypeVar, Concatenate, Union, List

"""
See: https://docs.python.org/3/library/functools.html
See: https://www.blog.pythonlibrary.org/2016/07/26/python-3-an-intro-to-asyncio/
See: https://stackoverflow.com/questions/47060133/python-3-type-hinting-for-decorator
"""

# OS Setup ----------------------------------------------------------------------
# Needed for spyder
# https://github.com/spyder-ide/spyder/issues/7096
import os


# Environment Setup ------------------------------------------------------------

def is_notebook():
    """
    Enable event loop within jupyter Notebook
    :return:
    """
    try:
        from IPython import get_ipython
    except:
        return False
    try:
        if "IPKernelApp" not in get_ipython().config:  # pragma: no cover
            raise ImportError("console")
    except:
        return False
    else:  # pragma: no cover
        return True


def is_spyder():
    return 'SPY_PYTHONPATH' in os.environ


if is_spyder() or is_notebook():
    logging.warning("nest_asyncio for Spyder or Jupyter environment activated")
    import nest_asyncio

    nest_asyncio.apply()

# Event Loop Setup ---------------------------------------------------
if os.name == "nt":  # Windows policies
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------

Param = ParamSpec("Param")
RetType = TypeVar("RetType")

OriginalFunction = Callable[Param, RetType]
DecoratedFunc = Callable[Concatenate[str, Param], RetType]


class SyncAsync(abc.ABC):

    def __init__(self, loop=None, parent=None):
        self._loop = loop
        self._parent = parent

    @staticmethod
    def sync(foo: OriginalFunction) -> Union[RetType, Callable[[ParamSpec], Awaitable[RetType]]]:
        """
        Convert an async method into a synchronous one
        :param foo:
        :return:
        """

        def _sync_async_decorator(_self, *args, **kwargs) -> RetType:
            """
            Decorated function
            :param _self:
            :param args:
            :param kwargs:
            :return:
            """
            if _self.loop.is_running():
                # If the even loop is already running, execute foo directly
                return foo(_self, *args, **kwargs)

            # Return vector, first element is either exception or foo result,
            # second determines which, False means exception
            res = [None, False]

            async def _runnable():
                # Async function to be executed
                try:
                    foo_result = await foo(_self, *args, **kwargs)
                except Exception as ex:
                    # If an exception occurs
                    res[:] = ex, False
                else:
                    # If the function was successful
                    res[:] = foo_result, True
                # Terminate the event loop
                _self.loop.stop()

            # Start eventloop, has to be stopped within _runnable()
            _self.loop.call_soon(lambda: asyncio.ensure_future(_runnable()))
            _self.loop.run_forever()
            if res[1]:  # If successful, return foo result
                return res[0]
            # Else, raise exception
            raise res[0]

        # Return decorated function
        return _sync_async_decorator

    @property
    def loop(self):
        """
        Returns event, loop, creates one if not yet set
        :return:
        """
        if self._parent:  # Get event loop from parent, if one exists
            return self._parent.loop
        if self._loop is None:  # If there is no event loop, create one
            self._loop = asyncio.get_event_loop()
        return self._loop
