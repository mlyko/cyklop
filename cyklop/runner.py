import abc
import asyncio
import importlib.util

from .log import logger
from .collector import Collector
from .scenario import User, Scenario


class ScenarioRunner:
    def __init__(self, scenario_file: str, collector: Collector = None):
        self.collector = collector

        self._loop = asyncio.get_event_loop()
        self._scenario = self._load_scenario(scenario_file)

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
