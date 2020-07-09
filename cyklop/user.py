import asyncio
from abc import ABC, abstractmethod

from .collector import Collector
from .client import HttpClient


class User(ABC):
    index = 0

    client_class = None

    def __init__(self, collector: Collector, loop: asyncio.AbstractEventLoop):
        self._loop = loop

        self.index += 1
        User.index = self.index

        self.client = self.client_class(self, collector, self._loop)

    def __str__(self):
        return f'{self.__class__.__name__}_{self.index}'

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.index})>'

    def pause(self, duration: float):
        return asyncio.sleep(duration, loop=self._loop)

    @abstractmethod
    async def execute(self):
        pass


class HttpUser(User):
    client_class = HttpClient
