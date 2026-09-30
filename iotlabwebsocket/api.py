"""Client class for REST API."""

import asyncio
import json
import math
import time
from dataclasses import dataclass, field

import tornado
from tornado.httpclient import AsyncHTTPClient

from . import DEFAULT_API_HOST, DEFAULT_API_PORT

# Maximum number of simultaneous requests to the API. Each websocket
# connection needs API answers before being accepted: with the shared
# Tornado client (10 requests at a time), the connections opened together
# by a user were accepted in batches, and the requests queued for more
# than 20 seconds failed.
API_MAX_CLIENTS = 50
# Lifetime of the API answers kept for an experiment (seconds). The
# websockets opened together for the nodes of an experiment all need the
# same token and node list: they share one request per resource instead of
# sending one each.
API_CACHE_TTL = 30


@dataclass
class _CachedResponse:
    """API answer shared by the requests of an experiment resource."""

    future: asyncio.Future
    # Set when the answer is received: an answer still pending is shared
    expires: float = math.inf


@dataclass
class ApiClient:
    """Class that store information about the REST API."""

    protocol: str
    host: str = DEFAULT_API_HOST
    port: str = DEFAULT_API_PORT
    username: str = ""
    password: str = ""
    _http_client: AsyncHTTPClient | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _cache: dict[tuple[str, str], _CachedResponse] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )

    @property
    def url(self) -> str:
        """Returns the base URL for experiments in the API."""
        return f"{self.protocol}://{self.host}:{self.port}/api/experiments"

    def _client(self) -> AsyncHTTPClient:
        # Created on first use, so that it is bound to the running IOLoop
        if self._http_client is None:
            self._http_client = AsyncHTTPClient(
                force_instance=True, max_clients=API_MAX_CLIENTS
            )
        return self._http_client

    async def _fetch_async(
        self, request: tornado.httpclient.HTTPRequest
    ) -> bytes:
        request.headers["Content-Type"] = "application/json"
        response = await self._client().fetch(request)
        return response.buffer.read()

    def _request(
        self, exp_id: str, resource: str
    ) -> tornado.httpclient.HTTPRequest:
        _url = f"{self.url}/{exp_id}/{resource}"
        kwargs = {}
        if self.username and self.password:
            kwargs.update(
                {
                    "auth_username": self.username,
                    "auth_password": self.password,
                }
            )
        return tornado.httpclient.HTTPRequest(_url, **kwargs)

    async def _fetch_cached(self, exp_id: str, resource: str) -> bytes:
        key = (exp_id, resource)
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached is None or cached.expires <= now:
            self._drop_expired(now)
            cached = _CachedResponse(
                asyncio.ensure_future(
                    self._fetch_async(self._request(exp_id, resource))
                )
            )
            self._cache[key] = cached
            cached.future.add_done_callback(
                lambda future: self._on_fetched(key, cached, future)
            )
        # A websocket connection that gives up does not cancel the request
        # shared with the others.
        return await asyncio.shield(cached.future)

    def _on_fetched(
        self, key: tuple[str, str], cached: _CachedResponse, future
    ) -> None:
        if future.cancelled() or future.exception() is not None:
            # Errors are not kept: the next connection asks the API again
            if self._cache.get(key) is cached:
                del self._cache[key]
            return
        cached.expires = time.monotonic() + API_CACHE_TTL

    def _drop_expired(self, now: float) -> None:
        expired = [
            key for key, cached in self._cache.items() if cached.expires <= now
        ]
        for key in expired:
            del self._cache[key]

    @staticmethod
    def _parse_nodes_response(response: str) -> list[str]:
        return json.loads(response)["nodes"]

    async def fetch_nodes_async(self, exp_id: str) -> list[str]:
        """Fetch the list of nodes using an asynchronous call."""
        response = await self._fetch_cached(exp_id, "")
        return ApiClient._parse_nodes_response(response.decode())

    async def fetch_token_async(self, exp_id: str) -> str:
        """Fetch the experiment token using an asynchronous call."""
        response = await self._fetch_cached(exp_id, "token")
        return json.loads(response.decode())["token"]
