from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type

from .user import User


@dataclass
class LoadStep:
    __slots__ = ['number', 'duration', 'user']

    number: int
    duration: float
    user: Type[User]


class Scenario(ABC):
    default_user: Type[User] = None

    def __init__(self):
        self._steps = []

    def ramp_up(self, number: int, duration: float, user: Type[User] = None):
        self._steps.append(LoadStep(number, duration,
                                    user or self.default_user))

    def jump_to(self, number: int, user: Type[User] = None):
        self._steps.append(LoadStep(number, 0.0,
                                    user or self.default_user))

    def hold_for(self, duration: float, user: Type[User] = None):
        self._steps.append(LoadStep(0, duration,
                                    user or self.default_user))

    @abstractmethod
    def simulate(self):
        pass
