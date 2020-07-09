import os
import time

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

    _reset_timer = None
    _log_timer = None

    _results_file = None

    def __init__(self, result_dir: str, file_name: str):
        self._file_path = os.path.join(result_dir, file_name)

        self.current_counters = self._create_counters()
        self.previous_counters = self._create_counters()
        self.total_counters = self._create_counters()

        self.results = []

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    @staticmethod
    def _create_counters():
        return {
            'active_users': 0,
            'users_done': 0,
            'requests_sent': 0,
            'requests_done': 0
        }

    def _reset_counters(self):
        self.previous_counters = self.current_counters
        self.current_counters = self._create_counters()
        self.current_counters['active_users'] = self.total_counters['active_users']

    def _write_result(self, result: Result):
        if not self._results_file:
            return
        self._results_file.write(f'{result}\n')

    @property
    def duration(self):
        if not self._start_time:
            return 0
        if self._end_time:
            return int(self._end_time - self._start_time)

        return int(time.time() - self._start_time)

    def start(self):
        self._results_file = open(self._file_path, 'w')
        self._start_time = time.time()

    def stop(self):
        self._end_time = time.time()
        if self._results_file:
            self._results_file.close()

    def start_user(self):
        self.current_counters['active_users'] += 1
        self.total_counters['active_users'] += 1

    def stop_user(self):
        self.current_counters['active_users'] -= 1
        self.total_counters['active_users'] -= 1
        self.current_counters['users_done'] += 1
        self.total_counters['users_done'] += 1

    def start_request(self):
        self.current_counters['requests_sent'] += 1
        self.total_counters['requests_sent'] += 1

    def stop_request(self, result: Result):
        self._write_result(result)
        self.results.append(result)
        self.current_counters['requests_done'] += 1
        self.total_counters['requests_done'] += 1
