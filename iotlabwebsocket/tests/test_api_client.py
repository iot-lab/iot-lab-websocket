"""iotlab-websocket api client."""

import unittest

from tornado.testing import AsyncHTTPTestCase, gen_test

from iotlabwebsocket.api import ApiClient
from iotlabwebsocket.handlers.http_handler import NODES
from iotlabwebsocket.web_application import WebApplication


class TestApiClientAsync(AsyncHTTPTestCase):
    def get_app(self):
        return WebApplication(self.api, use_local_api=True, token="token")

    def setUp(self):
        self.api = ApiClient("http")
        super().setUp()
        self.api.port = self.get_http_port()

    @gen_test
    async def test_fetch_nodes_async(self):
        nodes = await self.api.fetch_nodes_async("123")
        assert nodes == NODES["nodes"]

    @gen_test
    async def test_fetch_token_async(self):
        token = await self.api.fetch_token_async("123")
        assert token == "token"


class TestApiClientRequest(unittest.TestCase):
    def test_request(self):
        api = ApiClient("http")
        request = api._request("123", "token")
        assert request.url == f"{api.url}/123/token"
        assert request.auth_username is None

    def test_request_with_credentials(self):
        api = ApiClient("http", username="test", password="test")
        request = api._request("123", "")
        assert request.url == f"{api.url}/123/"
        assert request.auth_username == "test"
        assert request.auth_password == "test"
