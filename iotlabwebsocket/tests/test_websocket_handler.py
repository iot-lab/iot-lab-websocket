"""iotlabwebsocket websocket handler tests."""

import asyncio
import json
from unittest.mock import patch

import pytest
import tornado
from tornado.testing import AsyncHTTPTestCase, gen_test

from iotlabwebsocket.api import ApiClient
from iotlabwebsocket.handlers.websocket_handler import WebsocketClientHandler
from iotlabwebsocket.web_application import WebApplication


@patch("iotlabwebsocket.web_application.WebApplication.handle_websocket_open")
class TestWebsocketHandler(AsyncHTTPTestCase):
    def get_app(self):
        return WebApplication(self.api, use_local_api=True, token="token")

    def setUp(self):
        self.api = ApiClient("http")
        super().setUp()
        self.api.port = self.get_http_port()

    @patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    async def test_websocket_connection_raw(self, nodes, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial/raw"
        nodes.return_value = json.dumps({"nodes": ["node-1.local"]})

        connection = await tornado.websocket.websocket_connect(
            url, subprotocols=["user", "token", "token"]
        )
        assert connection.selected_subprotocol == "token"

        # if handle_websocket_open is called, the connection have passed all
        # checks with success
        ws_open.assert_called_once()

        with patch(
            "iotlabwebsocket.web_application"
            ".WebApplication.handle_websocket_data"
        ) as ws_data:
            data = b"test"
            await connection.write_message(data, binary=True)
            await asyncio.sleep(0.1)
            ws_data.assert_called_once()
            args, _ = ws_data.call_args
            assert len(args) == 2
            assert isinstance(args[0], WebsocketClientHandler)
            assert args[1] == data
            ws_handler = args[0]

            # Check some websocket handler internal methods (just for coverage)
            assert ws_handler.check_origin("http://localhost") is True
            assert (
                ws_handler.check_origin("https://devwww.iot-lab.info") is True
            )
            assert ws_handler.select_subprotocol(["test", ""]) is None
            assert (
                ws_handler.select_subprotocol(["user", "token", "aaaa"])
                == "token"
            )
            assert ws_handler.user == "user"
            assert not ws_handler.text

        with patch(
            "iotlabwebsocket.web_application"
            ".WebApplication.handle_websocket_close"
        ) as ws_close:
            connection.close(code=1000, reason="client exit")
            await asyncio.sleep(0.1)
            ws_close.assert_called_once()
            ws_close.assert_called_with(ws_handler)

    @patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    async def test_websocket_connection_text(self, nodes, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial"
        nodes.return_value = json.dumps({"nodes": ["node-1.local"]})

        connection = await tornado.websocket.websocket_connect(
            url, subprotocols=["user", "token", "token"]
        )
        assert connection.selected_subprotocol == "token"

        # if handle_websocket_open is called, the connection have passed all
        # checks with success
        ws_open.assert_called_once()

        with patch(
            "iotlabwebsocket.web_application"
            ".WebApplication.handle_websocket_data"
        ) as ws_data:
            data = "test"
            await connection.write_message(data)
            await asyncio.sleep(0.1)
            ws_data.assert_called_once()
            args, _ = ws_data.call_args
            assert len(args) == 2
            assert isinstance(args[0], WebsocketClientHandler)
            assert args[1] == data.encode("utf-8")
            ws_handler = args[0]

            # Check some websocket handler internal methods (just for coverage)
            assert ws_handler.check_origin("http://localhost") is True
            assert (
                ws_handler.check_origin("https://devwww.iot-lab.info") is True
            )
            assert ws_handler.select_subprotocol(["test", ""]) is None
            assert (
                ws_handler.select_subprotocol(["user", "token", "aaaa"])
                == "token"
            )
            assert ws_handler.user == "user"
            assert ws_handler.text

        with patch(
            "iotlabwebsocket.web_application"
            ".WebApplication.handle_websocket_close"
        ) as ws_close:
            connection.close(code=1000, reason="client exit")
            await asyncio.sleep(0.1)
            ws_close.assert_called_once()
            ws_close.assert_called_with(ws_handler)

    @patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    async def test_websocket_connection_text_invalid(self, nodes, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial"
        nodes.return_value = json.dumps({"nodes": ["node-1.local"]})

        connection = await tornado.websocket.websocket_connect(
            url, subprotocols=["user", "token", "token"]
        )
        assert connection.selected_subprotocol == "token"

        # if handle_websocket_open is called, the connection have passed all
        # checks with success
        ws_open.assert_called_once()

        with patch(
            "iotlabwebsocket.web_application"
            ".WebApplication.handle_websocket_data"
        ) as ws_data:
            data = "test"
            await connection.write_message(data)
            await asyncio.sleep(0.1)
            ws_data.assert_called_once()
            args, _ = ws_data.call_args
            assert len(args) == 2
            assert isinstance(args[0], WebsocketClientHandler)
            assert args[1] == data.encode("utf-8")

            ws_data.reset_mock()
            data = b"\xaa\xbb\xcc\xff"
            await connection.write_message(data, binary=True)
            await asyncio.sleep(0.1)
            assert ws_data.call_count == 0

    @gen_test
    async def test_websocket_connection_invalid_url(self, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local///serial"

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = await tornado.websocket.websocket_connect(url)
        assert "HTTP 404: Not Found" in str(exc_info.value)
        assert ws_open.call_count == 0

    @gen_test
    async def test_websocket_connection_invalid_subprotocol(self, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-123/serial"

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = await tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "invalid"]
            )
        assert "HTTP 401: Unauthorized" in str(exc_info.value)
        assert ws_open.call_count == 0

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = await tornado.websocket.websocket_connect(
                url, subprotocols=["user", "invalid", "invalid"]
            )
        assert "HTTP 401: Unauthorized" in str(exc_info.value)
        assert ws_open.call_count == 0

    @gen_test
    async def test_websocket_connection_invalid_node(self, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/invalid-123/serial"

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = await tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "token"]
            )
        assert "HTTP 401: Unauthorized" in str(exc_info.value)
        assert ws_open.call_count == 0

        url = f"ws://localhost:{self.api.port}/ws/invalid/123/localhost/serial"

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = await tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "token"]
            )
        assert "HTTP 401: Unauthorized" in str(exc_info.value)
        assert ws_open.call_count == 0

    @gen_test
    async def test_websocket_connection_api_errors(self, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial"
        fetch_token = "iotlabwebsocket.api.ApiClient.fetch_token_async"

        # Experiment refused by the API
        with patch(
            fetch_token,
            side_effect=tornado.httpclient.HTTPClientError(404),
        ):
            with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
                _ = await tornado.websocket.websocket_connect(
                    url, subprotocols=["user", "token", "token"]
                )
        assert "HTTP 401: Unauthorized" in str(exc_info.value)

        # API not reachable
        with patch(fetch_token, side_effect=ConnectionRefusedError()):
            with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
                _ = await tornado.websocket.websocket_connect(
                    url, subprotocols=["user", "token", "token"]
                )
        assert "HTTP 503: Service Unavailable" in str(exc_info.value)
        assert ws_open.call_count == 0

    @patch("iotlabwebsocket.handlers.http_handler._nodes")
    @patch(
        "iotlabwebsocket.api.ApiClient.fetch_token_async",
        return_value="s3cr3t-valid",
    )
    @gen_test
    async def test_websocket_tokens_not_logged(self, _, nodes, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial"
        nodes.return_value = json.dumps({"nodes": ["node-1.local"]})

        with self.assertLogs("iotlabwebsocket", level="DEBUG") as logs:
            _ = await tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "s3cr3t-valid"]
            )
            with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
                _ = await tornado.websocket.websocket_connect(
                    url, subprotocols=["user", "token", "s3cr3t-wrong"]
                )

        assert b"s3cr3t" not in exc_info.value.response.body
        assert not any("s3cr3t" in line for line in logs.output)

    @patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    async def test_websocket_api_requests_together(self, nodes, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial"
        nodes.return_value = json.dumps({"nodes": ["node-1.local"]})
        pending = []
        started = []

        def _slow(result):
            async def _fetch(_exp_id):
                pending.append(1)
                started.append(len(pending))
                await asyncio.sleep(0.05)
                pending.pop()
                return result

            return _fetch

        with (
            patch(
                "iotlabwebsocket.api.ApiClient.fetch_token_async",
                side_effect=_slow("token"),
            ),
            patch(
                "iotlabwebsocket.api.ApiClient.fetch_nodes_async",
                side_effect=_slow(["node-1.local"]),
            ),
        ):
            _ = await tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "token"]
            )

        # The token and nodes requests were pending at the same time
        assert max(started) == 2
        ws_open.assert_called_once()

    @patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    async def test_websocket_token_compared_in_constant_time(
        self, nodes, ws_open
    ):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial"
        nodes.return_value = json.dumps({"nodes": ["node-1.local"]})

        with patch(
            "iotlabwebsocket.handlers.websocket_handler.hmac.compare_digest",
            return_value=True,
        ) as compare:
            _ = await tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "other"]
            )
        compare.assert_called_once_with(b"other", b"token")
        ws_open.assert_called_once()
