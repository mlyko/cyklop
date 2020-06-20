from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LoadStep:
    __slots__ = ['number', 'duration']

    number: int
    duration: float


class Scenario(ABC):
    def __init__(self):
        self._steps = []

    def ramp_up(self, number: int, duration: float):
        self._steps.append(LoadStep(number, duration))

    def jump_to(self, number: int):
        self._steps.append(LoadStep(number, 0.0))

    def hold_for(self, duration: float):
        self._steps.append(LoadStep(0, duration))

    @abstractmethod
    def simulate(self):
        pass
