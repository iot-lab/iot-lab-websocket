"""Client class for REST API."""

import json

import tornado

from . import DEFAULT_API_HOST, DEFAULT_API_PORT


class ApiClient:
    """Class that store information about the REST API."""

    def __init__(
        self,
        protocol,
        host=DEFAULT_API_HOST,
        port=DEFAULT_API_PORT,
        username="",
        password="",
    ):
        # pylint:disable=too-many-arguments
        self.protocol = protocol
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def __eq__(self, other):
        return (
            self.protocol == other.protocol
            and self.host == other.host
            and self.port == other.port
            and self.username == other.username
            and self.password == other.password
        )

    @property
    def url(self):
        """Returns the base URL for experiments in the API."""
        return f"{self.protocol}://{self.host}:{self.port}/api/experiments"

    @staticmethod
    def _fetch_sync(request):
        request.headers["Content-Type"] = "application/json"
        client = tornado.httpclient.HTTPClient()
        try:
            return client.fetch(request).buffer.read()
        finally:
            client.close()

    @staticmethod
    async def _fetch_async(request):
        request.headers["Content-Type"] = "application/json"
        client = tornado.httpclient.AsyncHTTPClient()
        response = await client.fetch(request)
        return response.buffer.read()

    def _request(self, exp_id, resource):
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
    def _parse_nodes_response(response):
        return json.loads(response)["nodes"]

    def fetch_nodes_sync(self, exp_id):
        """Fetch the list of nodes using a synchronous call."""
        response = ApiClient._fetch_sync(self._request(exp_id, ""))
        return ApiClient._parse_nodes_response(response.decode())

    async def fetch_nodes_async(self, exp_id):
        """Fetch the list of nodes using an asynchronous call."""
        response = await ApiClient._fetch_async(self._request(exp_id, ""))
        return ApiClient._parse_nodes_response(response.decode())

    def fetch_token_sync(self, exp_id):
        """Fetch the experiment token using a synchronous call."""
        response = ApiClient._fetch_sync(self._request(exp_id, "token"))
        return json.loads(response.decode())["token"]

    async def fetch_token_async(self, exp_id):
        """Fetch the experiment token using an asynchronous call."""
        response = await ApiClient._fetch_async(self._request(exp_id, "token"))
        return json.loads(response.decode())["token"]
