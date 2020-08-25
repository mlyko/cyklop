import os
import json
import time
import asyncio

from .log import logger

STATUS_SUCCESS = 'OK'
STATUS_FAILURE = 'FAILED'
STATUS_ERROR = 'ERROR'

RESULTS_FILE = 'results.log'


class Result:
    __slots__ = [
        'name',
        'user',
        'start',
        'end',
        'status',
        'error'
    ]

    def __init__(self, name: str, user: str,
                 start: float = None, end: float = None,
                 status: str = STATUS_SUCCESS, error: str = None):
        self.name = name
        self.user = user
        self.start = start
        self.end = end
        self.status = status
        self.error = error

    def __bool__(self):
        return self.status == STATUS_SUCCESS

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.status})>'

    def __str__(self):
        return f'{self.user} {self.name} {self.start} {self.end} {self.status} {self.error or ""}'.rstrip()

    def set_failure(self, error=None):
        self.status = STATUS_FAILURE
        self.error = error and str(error)

    def set_error(self, error=None):
        self.status = STATUS_ERROR
        self.error = error and str(error)


class Collector:
    _start_time = None
    _end_time = None
    _collecting = False

    _reset_timer = None
    _log_timer = None

    _results_file = None

    def __init__(self, result_dir: str,
                 file_name: str = RESULTS_FILE,
                 log_interval: float = 15.0,
                 loop: asyncio.AbstractEventLoop = None):
        self._file_path = os.path.join(result_dir, file_name)
        self._log_interval = log_interval
        self._loop = loop or asyncio.get_event_loop()

        self.results = []

        self.current_counters = self._create_counters()
        self.previous_counters = self._create_counters()
        self.total_counters = self._create_counters()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _create_counters(self):
        return {
            'active_users': 0,
            'users_done': 0,
            'requests_sent': 0,
            'requests_done': 0,
            'responses': {
                STATUS_SUCCESS: 0,
                STATUS_FAILURE: 0,
                STATUS_ERROR: 0
            },
            'results_idx': len(self.results)
        }

    def _reset_counters(self):
        self._reset_timer = self._loop.call_later(1, self._reset_counters)

        self.previous_counters = self.current_counters
        self.current_counters = self._create_counters()

        self._results_file.write('@')
        json.dump(self.total_counters, self._results_file, separators=(",", ":"))
        self._results_file.write(os.linesep)

    def _write_result(self, result: Result):
        if not self._results_file:
            return
        self._results_file.write(f'{result}')
        self._results_file.write(os.linesep)

    def _log_progress(self):
        self._log_timer = self._loop.call_later(self._log_interval, self._log_progress)

        counters = self.previous_counters
        total_counters = self.total_counters

        total_time = 0.0
        min_time = 0.0
        max_time = 0.0
        start_idx = counters['results_idx']
        end_idx = self.current_counters['results_idx']
        if start_idx == end_idx:
            return

        for result in self.results[start_idx:end_idx]:
            response_time = result.end - result.start
            total_time += response_time
            if response_time < min_time or not min_time:
                min_time = response_time
            elif response_time > max_time:
                max_time = response_time

        responses = ', '.join([
            f'{key}={count} [{100 * count / total_counters["requests_done"]:.2f}%]'
            for key, count in total_counters["responses"].items()
        ])
        avg_time = total_time / (end_idx - start_idx)

        logger.info(f'After {self.duration} seconds\n'
                    f'\tUsers: active={total_counters["active_users"]} [{counters["active_users"]} user/s], '
                    f'done={total_counters["users_done"]} [{counters["users_done"]} user/s]\n'
                    f'\tRequests: sent={total_counters["requests_sent"]} [{counters["requests_sent"]} req/s] '
                    f'done={total_counters["requests_done"]} [{counters["requests_done"]} res/s]\n'
                    f'\tResponses: {responses}\n'
                    f'\tTimes: min={min_time:.3f}s, avg={avg_time:.3f}s, max={max_time:.3f}s')

    @property
    def duration(self):
        if not self._start_time:
            return 0
        if self._end_time:
            return int(self._end_time - self._start_time)

        return int(time.time() - self._start_time)

    def open(self):
        self._results_file = open(self._file_path, 'w')
        self._collecting = True
        self._start_time = time.time()
        self._reset_timer = self._loop.call_later(1, self._reset_counters)
        self._log_timer = self._loop.call_later(self._log_interval, self._log_progress)

    def close(self):
        self._end_time = time.time()
        self._collecting = False
        if self._reset_timer:
            self._reset_timer.cancel()
        if self._log_timer:
            self._log_timer.cancel()
        if self._results_file:
            self._results_file.close()
            self._results_file = None

    def start_user(self):
        if not self._collecting:
            return

        self.current_counters['active_users'] += 1
        self.total_counters['active_users'] += 1

    def stop_user(self):
        if not self._collecting:
            return

        self.total_counters['active_users'] -= 1
        self.current_counters['users_done'] += 1
        self.total_counters['users_done'] += 1

    def start_request(self):
        if not self._collecting:
            return

        self.current_counters['requests_sent'] += 1
        self.total_counters['requests_sent'] += 1

    def stop_request(self, result: Result):
        if not self._collecting:
            return

        self._write_result(result)
        self.results.append(result)
        self.current_counters['requests_done'] += 1
        self.current_counters['responses'][result.status] += 1
        self.total_counters['requests_done'] += 1
        self.total_counters['responses'][result.status] += 1
