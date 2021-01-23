"""iotlabwebsocket websocket handler tests."""

import json

import pytest

from mock import patch

import tornado
from tornado import gen
from tornado.testing import AsyncHTTPTestCase, gen_test

from iotlabwebsocket.api import ApiClient
from iotlabwebsocket.web_application import WebApplication
from iotlabwebsocket.handlers.websocket_handler import WebsocketClientHandler


@patch("iotlabwebsocket.web_application.WebApplication.handle_websocket_open")
class TestWebsocketHandler(AsyncHTTPTestCase):
    def get_app(self):
        return WebApplication(self.api, use_local_api=True, token="token")

    def setUp(self):
        self.api = ApiClient("http")
        super(TestWebsocketHandler, self).setUp()
        self.api.port = self.get_http_port()

    @patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    def test_websocket_connection_raw(self, nodes, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial/raw"
        nodes.return_value = json.dumps({"nodes": ["node-1.local"]})

        connection = yield tornado.websocket.websocket_connect(
            url, subprotocols=["user", "token", "token"]
        )
        assert connection.selected_subprotocol == "token"

        # if handle_websocket_open is called, the connection have passed all
        # checks with success
        ws_open.assert_called_once()

        with patch(
            "iotlabwebsocket.web_application" ".WebApplication.handle_websocket_data"
        ) as ws_data:
            data = b"test"
            yield connection.write_message(data, binary=True)
            yield gen.sleep(0.1)
            ws_data.assert_called_once()
            args, _ = ws_data.call_args
            assert len(args) == 2
            assert isinstance(args[0], WebsocketClientHandler)
            assert args[1] == data
            ws_handler = args[0]

            # Check some websocket handler internal methods (just for coverage)
            assert ws_handler.check_origin("http://localhost") is True
            assert ws_handler.check_origin("https://devwww.iot-lab.info") is True
            assert ws_handler.select_subprotocol(["test", ""]) is None
            assert ws_handler.select_subprotocol(["user", "token", "aaaa"]) == "token"
            assert ws_handler.user == "user"
            assert not ws_handler.text

        with patch(
            "iotlabwebsocket.web_application" ".WebApplication.handle_websocket_close"
        ) as ws_close:
            connection.close(code=1000, reason="client exit")
            yield gen.sleep(0.1)
            ws_close.assert_called_once()
            ws_close.assert_called_with(ws_handler)

    @patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    def test_websocket_connection_text(self, nodes, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial"
        nodes.return_value = json.dumps({"nodes": ["node-1.local"]})

        connection = yield tornado.websocket.websocket_connect(
            url, subprotocols=["user", "token", "token"]
        )
        assert connection.selected_subprotocol == "token"

        # if handle_websocket_open is called, the connection have passed all
        # checks with success
        ws_open.assert_called_once()

        with patch(
            "iotlabwebsocket.web_application" ".WebApplication.handle_websocket_data"
        ) as ws_data:
            data = "test"
            yield connection.write_message(data)
            yield gen.sleep(0.1)
            ws_data.assert_called_once()
            args, _ = ws_data.call_args
            assert len(args) == 2
            assert isinstance(args[0], WebsocketClientHandler)
            assert args[1] == data.encode("utf-8")
            ws_handler = args[0]

            # Check some websocket handler internal methods (just for coverage)
            assert ws_handler.check_origin("http://localhost") is True
            assert ws_handler.check_origin("https://devwww.iot-lab.info") is True
            assert ws_handler.select_subprotocol(["test", ""]) is None
            assert ws_handler.select_subprotocol(["user", "token", "aaaa"]) == "token"
            assert ws_handler.user == "user"
            assert ws_handler.text

        with patch(
            "iotlabwebsocket.web_application" ".WebApplication.handle_websocket_close"
        ) as ws_close:
            connection.close(code=1000, reason="client exit")
            yield gen.sleep(0.1)
            ws_close.assert_called_once()
            ws_close.assert_called_with(ws_handler)

    @patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    def test_websocket_connection_text_invalid(self, nodes, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial"
        nodes.return_value = json.dumps({"nodes": ["node-1.local"]})

        connection = yield tornado.websocket.websocket_connect(
            url, subprotocols=["user", "token", "token"]
        )
        assert connection.selected_subprotocol == "token"

        # if handle_websocket_open is called, the connection have passed all
        # checks with success
        ws_open.assert_called_once()

        with patch(
            "iotlabwebsocket.web_application" ".WebApplication.handle_websocket_data"
        ) as ws_data:
            data = "test"
            yield connection.write_message(data)
            yield gen.sleep(0.1)
            ws_data.assert_called_once()
            args, _ = ws_data.call_args
            assert len(args) == 2
            assert isinstance(args[0], WebsocketClientHandler)
            assert args[1] == data.encode("utf-8")

            ws_data.call_count = 0
            data = b"\xaa\xbb\xcc\xff"
            yield connection.write_message(data, binary=True)
            yield gen.sleep(0.1)
            assert ws_data.call_count == 0

    @gen_test
    def test_websocket_connection_invalid_url(self, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local///serial"

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = yield tornado.websocket.websocket_connect(url)
        assert "HTTP 404: Not Found" in str(exc_info.value)
        assert ws_open.call_count == 0

    @gen_test
    def test_websocket_connection_invalid_subprotocol(self, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-123/serial"

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = yield tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "invalid"]
            )
        assert "HTTP 401: Unauthorized" in str(exc_info.value)
        assert ws_open.call_count == 0

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = yield tornado.websocket.websocket_connect(
                url, subprotocols=["user", "invalid", "invalid"]
            )
        assert "HTTP 401: Unauthorized" in str(exc_info.value)
        assert ws_open.call_count == 0

    @gen_test
    def test_websocket_connection_invalid_node(self, ws_open):
        url = f"ws://localhost:{self.api.port}/ws/local/123/invalid-123/serial"

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = yield tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "token"]
            )
        assert "HTTP 401: Unauthorized" in str(exc_info.value)
        assert ws_open.call_count == 0

        url = f"ws://localhost:{self.api.port}/ws/invalid/123/localhost/serial"

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = yield tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "token"]
            )
        assert "HTTP 401: Unauthorized" in str(exc_info.value)
        assert ws_open.call_count == 0
