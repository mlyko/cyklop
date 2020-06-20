STATUS_SUCCESS = 'OK'
STATUS_FAILURE = 'FAILED'
STATUS_ERROR = 'ERROR'


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

    def set_failure(self, error=None):
        self.status = STATUS_FAILURE
        self.error = error and str(error)

    def set_error(self, error=None):
        self.status = STATUS_ERROR
        self.error = error and str(error)


class Collector:
    def __init__(self):
        self._results = []

    def __iter__(self):
        return iter(self._results)

    def push(self, result: Result):
        self._results.append(result)
