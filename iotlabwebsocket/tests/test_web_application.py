"""iotlabwebsocket web application tests."""

import json

import pytest

import mock

import tornado
from tornado import gen
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado.testing import AsyncHTTPTestCase, gen_test, bind_unused_port

from iotlabwebsocket.api import ApiClient
from iotlabwebsocket.web_application import WebApplication
from iotlabwebsocket.handlers.websocket_handler import WebsocketClientHandler
from iotlabwebsocket.clients.tcp_client import NODE_TCP_PORT


class TCPServerStub(TCPServer):

    stream = None

    @gen.coroutine
    def handle_stream(self, stream, address):
        self.stream = stream
        while True:
            try:
                yield self.stream.read_bytes(1)
            except StreamClosedError:
                break


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

    @mock.patch('iotlabwebsocket.clients.tcp_client.TCPClient.send')
    @mock.patch('iotlabwebsocket.clients.tcp_client.TCPClient.stop')
    @mock.patch('iotlabwebsocket.clients.tcp_client.TCPClient.start')
    @mock.patch('iotlabwebsocket.handlers.http_handler._nodes')
    @gen_test
    def test_tcp_connections_unit(self, nodes, start, stop, send):
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

    @mock.patch('iotlabwebsocket.handlers.http_handler._nodes')
    @gen_test
    def test_tcp_connection_server(self, nodes):
        url = ('ws://localhost:{}/ws/local/123/localhost/serial'
               .format(self.api.port))
        nodes.return_value = json.dumps({'nodes': ['localhost.local']})

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        websocket = yield tornado.websocket.websocket_connect(
            url, subprotocols=['token', 'token'])

        assert len(self.application.websockets['localhost']) == 1

        # Leave some time for the TCP connection to be ready
        yield gen.sleep(0.1)
        assert self.application.tcp_clients['localhost'].ready

        # Send some data
        websocket_srv = self.application.websockets['localhost'][0]
        websocket_srv.write_message = mock.Mock()
        yield server.stream.write(b"test")

        yield gen.sleep(0.1)
        assert websocket_srv.write_message.call_count == 1
        websocket_srv.write_message.call_count = 0

        # Smoke test to check that the websocket gets a message when the TCP
        # connection is not opened yet
        self.application.tcp_clients['localhost'].ready = False
        websocket.write_message(b'test')
        yield gen.sleep(0.1)
        websocket_srv.write_message.assert_called_with(
            "No TCP connection opened, cannot send message 'test'.\n")
        self.application.tcp_clients['localhost'].ready = True

        # Force close from TCP server, all websockets should be closed
        # automatically and TCP client connection as well
        server.stream.close()
        yield gen.sleep(0.1)

        assert not self.application.tcp_clients['localhost'].ready
        assert len(self.application.websockets['node-1']) == 0

    @mock.patch('iotlabwebsocket.handlers.http_handler._nodes')
    @gen_test
    def test_application_stop(self, nodes):
        url = ('ws://localhost:{}/ws/local/123/localhost/serial'
               .format(self.api.port))
        nodes.return_value = json.dumps({'nodes': ['localhost.local']})

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        for _ in range(10):
            _ = yield tornado.websocket.websocket_connect(
                url, subprotocols=['token', 'token'])

        assert len(self.application.websockets['localhost']) == 10

        self.application.stop()
        yield gen.sleep(0.1)
        assert len(self.application.websockets['localhost']) == 0
