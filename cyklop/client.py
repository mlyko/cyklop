import asyncio

import httpx

from .collector import Result, Collector


class HttpRequest:
    __slots__ = [
        '_client',
        'name',
        'method',
        'url',
        'params',
        'headers',
        'cookies',
        'timeout'
    ]

    def __init__(self, client, method: str, url: str, name: str = None,
                 params=None, headers=None, cookies=None):
        self._client = client
        self.name = name or f'[{method}]{url}'
        self.method = method
        self.url = url
        self.params = params or {}
        self.headers = headers or {}
        self.cookies = cookies or {}

        self.timeout: float = 10.0

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.name})>'

    def __await__(self):
        return self._client.request(self).__await__()


class HttpResponse:
    __slots__ = [
        '_request',
        'result',
        'status',
        'headers',
        'data',
        'encoding'
    ]

    def __init__(self, request: HttpRequest, result: Result,
                 status: int = -1, headers: dict = None,
                 data: bytes = None, encoding: str = 'utf-8'):
        self._request = request
        self.result = result
        self.status = status
        self.headers = headers or {}
        self.data = data
        self.encoding = encoding

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.status})>'

    @property
    def content(self) -> str:
        if not self.data:
            return ''
        return self.data.decode(self.encoding)

    def verify_status(self, *statuses):
        if self.status not in statuses:
            self.result.set_failure()

    def verify_header(self, header, value):
        if self.headers.get(header) != value:
            self.result.set_failure()


class HttpClient:
    base_url: str = None

    auth = None
    ssl_verify: bool = False
    ssl_cert: str = None

    _client = None

    def __init__(self, user: 'User', collector: Collector, loop: asyncio.AbstractEventLoop):
        self.headers = {}
        self.cookies = {}
        self._user = user
        self._collector = collector
        self._loop = loop

    def _build_url(self, path: str):
        return f'{self.base_url}{path}' if self.base_url else path

    def _get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url,
                                             headers=self.headers,
                                             cookies=self.cookies,
                                             auth=self.auth,
                                             verify=self.ssl_verify,
                                             cert=self.ssl_cert)
        return self._client

    def get(self, url: str, **kwargs) -> HttpRequest:
        return HttpRequest(self, 'GET', url, **kwargs)

    async def request(self, request: HttpRequest) -> HttpResponse:
        client = self._get_client()
        result = Result(request.name, str(self._user),
                        start=self._loop.time())
        try:
            self._collector.start_request()
            response = await client.request(request.method, request.url,
                                            params=request.params,
                                            headers=request.headers,
                                            cookies=request.cookies)
        except Exception as err:
            result.set_error(err)
            return HttpResponse(request, result)
        else:
            return HttpResponse(request, result,
                                response.status_code,
                                headers={**response.headers},
                                data=response.content, encoding=response.encoding)
        finally:
            result.end = self._loop.time()
            self._collector.stop_request(result)

    async def close(self):
        if self._client:
            await self._client.aclose()
