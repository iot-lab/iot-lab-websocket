"""Client class for REST API."""

import json
from dataclasses import dataclass

import tornado

from . import DEFAULT_API_HOST, DEFAULT_API_PORT


@dataclass
class ApiClient:
    """Class that store information about the REST API."""

    protocol: str
    host: str = DEFAULT_API_HOST
    port: str = DEFAULT_API_PORT
    username: str = ""
    password: str = ""

    @property
    def url(self) -> str:
        """Returns the base URL for experiments in the API."""
        return f"{self.protocol}://{self.host}:{self.port}/api/experiments"

    @staticmethod
    async def _fetch_async(request: tornado.httpclient.HTTPRequest) -> bytes:
        request.headers["Content-Type"] = "application/json"
        client = tornado.httpclient.AsyncHTTPClient()
        response = await client.fetch(request)
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

    @staticmethod
    def _parse_nodes_response(response: str) -> list[str]:
        return json.loads(response)["nodes"]

    async def fetch_nodes_async(self, exp_id: str) -> list[str]:
        """Fetch the list of nodes using an asynchronous call."""
        response = await ApiClient._fetch_async(self._request(exp_id, ""))
        return ApiClient._parse_nodes_response(response.decode())

    async def fetch_token_async(self, exp_id: str) -> str:
        """Fetch the experiment token using an asynchronous call."""
        response = await ApiClient._fetch_async(self._request(exp_id, "token"))
        return json.loads(response.decode())["token"]
