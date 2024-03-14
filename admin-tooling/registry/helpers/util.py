from pydantic import BaseModel
from typing import Dict, Any, Set
import json
from functools import wraps
from httpx import AsyncClient
import datetime as dt
from typing import Union
import asyncio


def py_to_dict(model: BaseModel) -> Dict[str, Any]:
    return json.loads(model.json(exclude_none=True))


_background_tasks: Set[asyncio.Task] = set()


class RateLimitedClient(AsyncClient):
    """httpx.AsyncClient with a rate limit.

    This wraps the AsyncClient from httpx and adds a rate limited semaphore.
    SOURCED FROM https://github.com/encode/httpx/issues/815

    This works by claiming the semaphore, scheduling the request, and then
    releasing it after the interval time. This is not exactly the same as
    minimising concurrent queries because the query might take longer than the
    interval.
    """

    def __init__(self, interval: Union[dt.timedelta, float], count: int = 1, **kwargs: Any):
        """
        Parameters
        ----------
        interval : Union[dt.timedelta, float]
            Length of interval.
            If a float is given, seconds are assumed.
        numerator : int, optional
            Number of requests which can be sent in any given interval (default 1).
        """
        if isinstance(interval, dt.timedelta):
            interval = interval.total_seconds()

        self.interval = interval
        self.semaphore = asyncio.Semaphore(count)
        super().__init__(**kwargs)

    def _schedule_semaphore_release(self) -> None:
        wait = asyncio.create_task(asyncio.sleep(self.interval))
        _background_tasks.add(wait)

        def wait_cb(task: asyncio.Task) -> None:
            self.semaphore.release()
            _background_tasks.discard(task)

        wait.add_done_callback(wait_cb)

    @wraps(AsyncClient.send)
    async def send(self, *args: Any, **kwargs: Any) -> Any:
        await self.semaphore.acquire()
        send = asyncio.create_task(super().send(*args, **kwargs))
        self._schedule_semaphore_release()
        return await send


slow_per_second = 5
fast_per_second = 30

timeout_seconds = 30

slow_session = RateLimitedClient(
    interval=1,
    count=slow_per_second,
    # passed through to AsyncClient
    timeout=float(timeout_seconds)
)
fast_session = RateLimitedClient(
    interval=1,
    count=fast_per_second,
    # passed through to AsyncClient
    timeout=float(timeout_seconds)
)
