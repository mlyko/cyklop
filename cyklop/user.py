import asyncio
from abc import ABC, abstractmethod

from .collector import Collector, Result
from .client import HttpClient


class User(ABC):
    index = 0

    def __init__(self, collector: Collector, loop=None):
        self._collector = collector
        self._loop = loop

        self.index += 1
        User.index = self.index

    def __str__(self):
        return f'{self.__class__.__name__}_{self.index}'

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.index})>'

    def collect(self, result: Result):
        self._collector.push(result)

    def pause(self, duration: float):
        return asyncio.sleep(duration, loop=self._loop)

    @abstractmethod
    async def execute(self):
        pass


class HttpUser(User):
    client_class = HttpClient

    def __init__(self, collector, loop=None):
        super().__init__(collector, loop)
        self.client = self.client_class(self, self._loop)
