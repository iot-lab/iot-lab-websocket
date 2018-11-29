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


@patch('iotlabwebsocket.web_application.WebApplication.handle_websocket_open')
class TestWebsocketHandler(AsyncHTTPTestCase):

    def get_app(self):
        return WebApplication(self.api, use_local_api=True, token='token')

    def setUp(self):
        self.api = ApiClient('http')
        super(TestWebsocketHandler, self).setUp()
        self.api.port = self.get_http_port()

    @patch('iotlabwebsocket.handlers.http_handler._nodes')
    @gen_test
    def test_websocket_connection(self, nodes, ws_open):
        url = ('ws://localhost:{}/ws/local/123/node-1/serial'
               .format(self.api.port))
        nodes.return_value = json.dumps({'nodes': ['node-1.local']})

        connection = yield tornado.websocket.websocket_connect(
            url, subprotocols=['token', 'token'])
        assert connection.selected_subprotocol == 'token'

        # if handle_websocket_open is called, the connection have passed all
        # checks with success
        ws_open.assert_called_once()

        with patch('iotlabwebsocket.web_application'
                   '.WebApplication.handle_websocket_data') as ws_data:
            data = "test"
            yield connection.write_message(data)
            yield gen.sleep(0.1)
            ws_data.assert_called_once()
            args, _ = ws_data.call_args
            assert len(args) == 2
            assert isinstance(args[0], WebsocketClientHandler)
            assert args[1] == data
            ws_handler = args[0]

            # Check some websocket handler internal methods (just for coverage)
            assert ws_handler.check_origin("http://localhost") is True
            assert ws_handler.check_origin(
                "https://devwww.iot-lab.info") is True
            assert ws_handler.select_subprotocol(['test', '']) is None
            assert ws_handler.select_subprotocol(['token', 'aaaa']) == 'token'

        with patch('iotlabwebsocket.web_application'
                   '.WebApplication.handle_websocket_close') as ws_close:
            connection.close(code=1000, reason="client exit")
            yield gen.sleep(0.1)
            ws_close.assert_called_once()
            ws_close.assert_called_with(ws_handler)

    @gen_test
    def test_websocket_connection_invalid_url(self, ws_open):
        url = ('ws://localhost:{}/ws/local///serial'
               .format(self.api.port))

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = yield tornado.websocket.websocket_connect(url)
        assert "HTTP 404: Not Found" in str(exc_info)
        assert ws_open.call_count == 0

    @gen_test
    def test_websocket_connection_invalid_subprotocol(self, ws_open):
        url = ('ws://localhost:{}/ws/local/123/node-123/serial'
               .format(self.api.port))

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = yield tornado.websocket.websocket_connect(
                url, subprotocols=['token', 'invalid'])
        assert "HTTP 401: Unauthorized" in str(exc_info)
        assert ws_open.call_count == 0

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = yield tornado.websocket.websocket_connect(
                url, subprotocols=['invalid', 'invalid'])
        assert "HTTP 401: Unauthorized" in str(exc_info)
        assert ws_open.call_count == 0

    @gen_test
    def test_websocket_connection_invalid_node(self, ws_open):
        url = ('ws://localhost:{}/ws/local/123/invalid-123/serial'
               .format(self.api.port))

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = yield tornado.websocket.websocket_connect(
                url, subprotocols=['token', 'token'])
        assert "HTTP 401: Unauthorized" in str(exc_info)
        assert ws_open.call_count == 0

        url = ('ws://localhost:{}/ws/invalid/123/localhost/serial'
               .format(self.api.port))

        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = yield tornado.websocket.websocket_connect(
                url, subprotocols=['token', 'token'])
        assert "HTTP 401: Unauthorized" in str(exc_info)
        assert ws_open.call_count == 0
