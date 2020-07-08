import os

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
    users = 0

    _results_file = None

    def __init__(self, result_dir: str, file_name: str):
        self._file_path = os.path.join(result_dir, file_name)
        self._results = []

    def __iter__(self):
        return iter(self._results)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _write_result(self, result: Result):
        if not self._results_file:
            return
        self._results_file.write(f'{result}\n')

    def open(self):
        self._results_file = open(self._file_path, 'w')

    def close(self):
        if self._results_file:
            self._results_file.close()

    def push(self, result: Result):
        self._results.append(result)
        self._write_result(result)
