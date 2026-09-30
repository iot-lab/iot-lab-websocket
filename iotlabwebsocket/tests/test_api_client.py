"""iotlab-websocket api client."""

import asyncio
import json
import unittest
from unittest import mock

import tornado.web
from tornado.httpclient import HTTPClientError
from tornado.testing import AsyncHTTPTestCase, gen_test

from iotlabwebsocket.api import API_MAX_CLIENTS, ApiClient
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


class SlowApiHandler(tornado.web.RequestHandler):
    """Fake API answering after a delay, recording concurrent requests."""

    pending = 0
    max_pending = 0

    async def get(self, _exp_id, _resource):
        cls = SlowApiHandler
        cls.pending += 1
        cls.max_pending = max(cls.max_pending, cls.pending)
        await asyncio.sleep(0.1)
        cls.pending -= 1
        self.finish(json.dumps({"token": "token"}))


class TestApiClientConcurrency(AsyncHTTPTestCase):
    def get_app(self):
        return tornado.web.Application(
            [(r"/api/experiments/(\d+)/(.*)", SlowApiHandler)]
        )

    def setUp(self):
        super().setUp()
        self.api = ApiClient("http", port=str(self.get_http_port()))

    @gen_test
    async def test_concurrent_requests(self):
        count = API_MAX_CLIENTS
        await asyncio.gather(
            *[self.api.fetch_token_async(str(i)) for i in range(count)]
        )

        # All the requests are sent together, not in batches
        assert SlowApiHandler.max_pending == count
        assert self.api._client() is self.api._client()


class CountingApiHandler(tornado.web.RequestHandler):
    """Fake API counting its requests, failing on demand."""

    requests = 0
    fail = False

    async def get(self, _exp_id, _resource):
        CountingApiHandler.requests += 1
        await asyncio.sleep(0.05)
        if CountingApiHandler.fail:
            self.set_status(503)
            self.finish("unavailable")
            return
        self.finish(json.dumps({"token": "token", "nodes": ["node-1.local"]}))


class TestApiClientCache(AsyncHTTPTestCase):
    def get_app(self):
        return tornado.web.Application(
            [(r"/api/experiments/(\d+)/(.*)", CountingApiHandler)]
        )

    def setUp(self):
        super().setUp()
        CountingApiHandler.requests = 0
        CountingApiHandler.fail = False
        self.api = ApiClient("http", port=str(self.get_http_port()))

    @gen_test
    async def test_requests_shared(self):
        # Requests sent together for an experiment share one API request
        tokens = await asyncio.gather(
            *[self.api.fetch_token_async("123") for _ in range(20)]
        )
        assert tokens == ["token"] * 20
        assert CountingApiHandler.requests == 1

        # The answer is kept for the next connections
        assert await self.api.fetch_token_async("123") == "token"
        assert CountingApiHandler.requests == 1

        # Other resources and experiments have their own requests
        assert await self.api.fetch_nodes_async("123") == ["node-1.local"]
        assert await self.api.fetch_token_async("456") == "token"
        assert CountingApiHandler.requests == 3

    @gen_test
    async def test_answer_expires(self):
        with mock.patch("iotlabwebsocket.api.API_CACHE_TTL", 0.01):
            await self.api.fetch_token_async("123")
            await asyncio.sleep(0.02)
            await self.api.fetch_token_async("123")
        assert CountingApiHandler.requests == 2

        # Expired answers are dropped from the cache
        await asyncio.sleep(0.02)
        await self.api.fetch_token_async("456")
        assert ("123", "token") not in self.api._cache

    @gen_test
    async def test_errors_not_kept(self):
        CountingApiHandler.fail = True
        results = await asyncio.gather(
            self.api.fetch_token_async("123"),
            self.api.fetch_token_async("123"),
            return_exceptions=True,
        )
        assert all(isinstance(r, HTTPClientError) for r in results)
        assert CountingApiHandler.requests == 1

        CountingApiHandler.fail = False
        assert await self.api.fetch_token_async("123") == "token"
        assert CountingApiHandler.requests == 2
