from abc import ABC, abstractmethod
from typing import Type

from .log import logger
from .user import User


class LoadStep:
    _start_time: float = None
    _end_time: float = None

    _base_rate: int = 0
    _rate_acc: float = 0.0

    def __init__(self, rate: int, duration: int, user: Type[User]):
        self.rate = rate if rate >= 1 else 0
        self.duration = duration if duration >= 1 else 0
        self.user = user

    def start(self, current_time: float, current_rate: int = 0):
        self._start_time = current_time
        self._end_time = current_time + self.duration
        self._base_rate = current_rate

        if self.rate and self.duration:
            self._rate_acc = (self.rate - self._base_rate) / self.duration

    def done(self, current_time: float) -> bool:
        return self._end_time <= current_time

    def get_rate(self, current_time: float) -> int:
        if not self.duration:
            return self.rate

        if not self.rate:
            return self._base_rate

        rate = self._base_rate + int(self._rate_acc * (current_time + 1.0 - self._start_time))
        return min(rate, self.rate)


class Scenario(ABC):
    default_user: Type[User] = None

    def __init__(self):
        self._steps = []

    def __iter__(self):
        for step in self._steps:
            yield step

    def ramp_up(self, rate: int, duration: int, user: Type[User] = None):
        user = user or self.default_user
        logger.info('Simulate ramp up user rate: user=%r, rate=%d, duration=%ds',
                    user, rate, duration)
        self._steps.append(LoadStep(rate, duration, user))

    def jump_to(self, rate: int, user: Type[User] = None):
        user = user or self.default_user
        logger.info('Simulate jump user rate to: user=%r, rate=%d', user, rate)
        self._steps.append(LoadStep(rate, 0, user))

    def hold_for(self, duration: int, user: Type[User] = None):
        user = user or self.default_user
        logger.info('Simulate hold user rate for: user=%r, duration=%ds', user, duration)
        self._steps.append(LoadStep(0, duration, user))

    @abstractmethod
    def simulate(self):
        pass
