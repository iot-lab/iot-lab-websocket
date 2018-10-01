"""iotlabwebsocket web application tests."""

import json

import pytest

from mock import patch

import tornado
from tornado import gen
from tornado.testing import AsyncHTTPTestCase, gen_test

from iotlabwebsocket.api import ApiClient
from iotlabwebsocket.web_application import WebApplication
from iotlabwebsocket.handlers.websocket_handler import WebsocketClientHandler


@patch('iotlabwebsocket.clients.tcp_client.TCPClient.send')
@patch('iotlabwebsocket.clients.tcp_client.TCPClient.stop')
@patch('iotlabwebsocket.clients.tcp_client.TCPClient.start')
class TestWebApplication(AsyncHTTPTestCase):

    def get_app(self):
        self.application = WebApplication(self.api, use_local_api=True,
                                          token='token')
        return self.application

    def setUp(self):
        self.api = ApiClient('http')
        super(TestWebApplication, self).setUp()
        self.api.port = self.get_http_port()

        assert len(self.application.websockets) == 0

    @patch('iotlabwebsocket.handlers.http_handler._nodes')
    @gen_test
    def test_tcp_connections(self, nodes, start, stop, send):
        url = ('ws://localhost:{}/ws/local/123/node-1/serial'
               .format(self.api.port))
        nodes.return_value = json.dumps({'nodes': ['node-1.local']})

        websocket = yield tornado.websocket.websocket_connect(
            url, subprotocols=['token', 'token'])

        assert len(self.application.websockets['node-1']) == 1

        start.assert_called_once()
        args, kwargs = start.call_args

        assert len(args) == 1
        assert args[0] == 'node-1'
        assert kwargs == dict(on_data=self.application.handle_tcp_data,
                              on_close=self.application.handle_tcp_close)

        # Forcing TCP client to be ready, just for the test
        self.application.tcp_clients['node-1'].ready = True

        # another websocket connection for the same node doesn't start a new
        # TCP connection
        start.call_count = 0
        websocket2 = yield tornado.websocket.websocket_connect(
            url, subprotocols=['token', 'token'])

        assert start.call_count == 0
        assert len(self.application.websockets['node-1']) == 2

        websocket2.close()
        yield gen.sleep(0.1)

        # There's still a websocket connection opened, so TCP client is not
        # closed
        assert stop.call_count == 0
        assert len(self.application.websockets['node-1']) == 1

        # Send some data
        websocket.write_message("test")
        yield gen.sleep(0.1)

        send.assert_called_once()
        send.assert_called_with(b"test")

        # Close last websocket
        websocket.close()
        yield gen.sleep(0.1)

        assert stop.call_count == 1
        assert len(self.application.websockets['node-1']) == 0
        assert 'node-1' not in self.application.tcp_clients
