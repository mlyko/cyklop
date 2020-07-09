import os
import abc
import asyncio
import importlib.util
from datetime import datetime
from asyncio.events import AbstractEventLoop

from .log import logger
from .collector import Collector
from .scenario import User, Scenario

RESULTS_DIR = 'results'


class ScenarioRunner:
    # Number of spawning cycles per second
    _spawn_cycles = 10
    _spawn_interval = 1 / _spawn_cycles
    _spawn_index = 0

    _scenario_steps = None
    _current_step = None
    _current_rate = 0
    _start_time: float = None

    _pending_users = 0

    _task = None

    def __init__(self, scenario_file: str, results_dir: str = RESULTS_DIR, loop: AbstractEventLoop = None):
        self._loop = loop or asyncio.get_event_loop()
        self._scenario = self._load_scenario(scenario_file)
        self._result_dir = self._create_result_dir(results_dir, scenario_file)

        self.collector = Collector(self._result_dir)

    @staticmethod
    def _load_scenario(scenario_file: str):
        logger.debug('Load scenario from file: %s', scenario_file)
        spec = importlib.util.spec_from_file_location('_scenario_file', scenario_file)
        scenario_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scenario_module)

        user_class = None
        scenario_class = None
        for attrib in vars(scenario_module).values():
            if type(attrib) is not abc.ABCMeta:
                continue

            if issubclass(attrib, User) and (not user_class or issubclass(attrib, user_class)):
                user_class = attrib
            elif issubclass(attrib, Scenario) and (not scenario_class or issubclass(attrib, scenario_class)):
                scenario_class = attrib

        if scenario_class is None:
            logger.error('Scenario class not found in file: %s', scenario_file)
            return None

        if scenario_class.default_user is None:
            scenario_class.default_user = user_class

        logger.info('Loaded scenario file: user=%r, scenario=%r', scenario_class.default_user, scenario_class)
        return scenario_class()

    @staticmethod
    def _create_result_dir(root_dir: str, scenario_file: str):
        dt = datetime.now()
        scenario_name = os.path.splitext(os.path.basename(scenario_file))
        result_dir = os.path.abspath(os.path.join(root_dir,
                                     f'{scenario_name}-{dt.strftime("%Y%m%d%H%M%S%f")}'))
        logger.info('Create scenario result dir: %s', result_dir)
        os.makedirs(result_dir, exist_ok=True)
        return result_dir

    def _step_forward(self, current_time: float):
        self._current_step = next(self._scenario_steps, None)
        if self._current_step:
            self._current_step.start(current_time, self._current_rate)

    def _rate_forward(self):
        timer = self._loop.call_later(1.0, self._rate_forward)

        current_time = self._loop.time()
        if self._current_step.done(current_time):
            self._step_forward(current_time)

        if self._current_step is None:
            timer.cancel()
            return

        self._current_rate = self._current_step.get_rate(current_time)
        logger.debug('Current users rate: %d', self._current_rate)
        self._spawn_index = 0

    def _spawn_users(self):
        if self._current_step is None:
            return

        self._loop.call_later(self._spawn_interval, self._spawn_users)

        n = self._current_rate // self._spawn_cycles
        if self._spawn_index % self._spawn_cycles < self._current_rate % self._spawn_cycles:
            n += 1

        logger.debug('Spawn next users: %d', n)
        for i in range(n):
            user = self._current_step.user(self.collector, self._loop)
            self.collector.start_user()
            future = asyncio.ensure_future(user.execute(), loop=self._loop)
            future.add_done_callback(self._user_done)
            self._pending_users += 1

        self._spawn_index += 1

    def _user_done(self, future):
        try:
            future.result()
        except Exception as err:
            logger.error('User execution error: %s', err)
        finally:
            self.collector.stop_user()

        self._pending_users -= 1
        if self._current_step is None and self._pending_users == 0:
            self._task.set_result(True)

    async def run(self):
        self._task = asyncio.ensure_future(asyncio.Future(loop=self._loop), loop=self._loop)

        self._scenario.simulate()
        self._scenario_steps = iter(self._scenario)

        self._start_time = self._loop.time()
        logger.info('Start running scenario: %s', self._scenario)
        self._step_forward(self._start_time)
        self._rate_forward()
        self._spawn_users()

        with self.collector:
            try:
                await self._task
            finally:
                logger.info('Stop running scenario: %s', self._scenario)
