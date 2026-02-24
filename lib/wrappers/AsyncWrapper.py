import time
import asyncio
from lib.common.logger import Logger
from typing import Callable


class AsyncWrapper:
    def __init__(self, service_name="AsyncWrapper"):
        self.service_name = service_name

    def retry(
        self,
        func: Callable,
        *args,
        max_retries=3,
        service_name: str = None,
        delay=1,
        **kwargs,
    ):
        for attempt in range(max_retries + 1):
            try:
                service_name = self.hanldel_change_service_name(service_name)
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries:
                    Logger.error(f"Max retries reached: {e}", self.service_name)
                    raise
                Logger.warning(
                    f"Retry {attempt + 1}/{max_retries} after error: {e}",
                    self.service_name,
                )
                time.sleep(delay)

    async def async_wrapper(
        self, func: Callable, *args, service_name: str = None, **kwargs
    ):
        try:
            service_name = self.hanldel_change_service_name(service_name)
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            Logger.error(f"Error in async wrapper: {e}", self.service_name)
            raise

    def set_service_name(self, service_name: str):
        self.service_name = service_name

    def hanldel_change_service_name(self, service_name):
        if service_name == None:
            return self.service_name
        else:
            self.service_name = service_name
            return self.service_name
