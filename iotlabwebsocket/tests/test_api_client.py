"""iotlab-websocket api client."""

import json
import io
import unittest
import mock

from tornado.testing import AsyncHTTPTestCase, gen_test

from iotlabwebsocket.api import ApiClient
from iotlabwebsocket.handlers.http_handler import NODES
from iotlabwebsocket.web_application import WebApplication


class TestApiClientAsync(AsyncHTTPTestCase):
    def get_app(self):
        return WebApplication(self.api, use_local_api=True, token="token")

    def setUp(self):
        self.api = ApiClient("http")
        super(TestApiClientAsync, self).setUp()
        self.api.port = self.get_http_port()

    @gen_test
    def test_fetch_nodes_async(self):
        nodes = yield self.api.fetch_nodes_async("123")
        assert nodes == NODES["nodes"]

    @gen_test
    def test_fetch_token_async(self):
        token = yield self.api.fetch_token_async("123")
        assert token == "token"


class ResponseBuffer(object):
    def __init__(self, buf):
        self.buffer = io.BytesIO(buf)


@mock.patch("tornado.httpclient.HTTPClient.fetch")
class TestApiClientSync(unittest.TestCase):
    def setUp(self):
        self.api = ApiClient("http")

    def test_fetch_token_sync(self, fetch):
        expected_json = json.dumps({"token": "token"})
        fetch.return_value = ResponseBuffer(expected_json.encode())
        token = self.api.fetch_token_sync("123")
        assert token == "token"

    def test_fetch_nodes_sync(self, fetch):
        fetch.return_value = ResponseBuffer(json.dumps(NODES).encode())
        nodes = self.api.fetch_nodes_sync("123")
        assert nodes == NODES["nodes"]

    @mock.patch("tornado.httpclient.HTTPRequest")
    def test_fetch_with_credentials(self, request, fetch):
        fetch.return_value = ResponseBuffer(json.dumps(NODES).encode())

        self.api = ApiClient("http", username="test", password="test")
        nodes = self.api.fetch_nodes_sync("123")

        args, kwargs = request.call_args
        assert len(args) == 1
        assert args[0] == "{}/{}/{}".format(self.api.url, "123", "")
        assert kwargs == dict(auth_username="test", auth_password="test")
        assert nodes == NODES["nodes"]
