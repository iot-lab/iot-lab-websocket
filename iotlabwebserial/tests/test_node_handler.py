"""iotlabwebserial node handler tests."""

import sys
import unittest

import mock

from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado import gen

from tornado.testing import AsyncTestCase, gen_test, bind_unused_port

from iotlabwebserial.node_handler import NodeHandler


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


class NodeHandlerTest(AsyncTestCase):

    @gen_test
    def test_tcp_connection(self):
        node_handler = NodeHandler(debug=True)

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(20000)

        # Connect to the TCP server stub
        yield node_handler.start_tcp_connection("localhost", 20000)
        assert node_handler.tcp_ready
        assert node_handler.tcp is not None
        assert node_handler.node == "localhost"

        # Preparing the websocket mock
        websocket_mock = mock.Mock()
        websocket_mock.close = mock.Mock(return_value=0)
        websocket_mock.write_message = mock.Mock(return_value=0)
        node_handler.websockets.append(websocket_mock)

        # String is sent via websocket character by character
        message = b"Hello World"
        server.stream.write(message)
        yield gen.sleep(0.01)
        assert websocket_mock.write_message.call_count == len(message)
        websocket_mock.write_message.call_count = 0

        # Non unicode data are not sent to the connected websockets
        message = b'\xAA\xBB'
        server.stream.write(message)
        yield gen.sleep(0.01)
        assert websocket_mock.write_message.call_count == 0

        # When the TCP connection is lost, all websockets are closed
        server.stream.close()
        yield gen.sleep(0.01)
        websocket_mock.close.assert_called_once()
        assert not node_handler.tcp_ready

    @gen_test
    def test_tcp_failed_connection(self):
        node_handler = NodeHandler(debug=True)

        # Cannot connect because TCP server is not running
        yield node_handler.start_tcp_connection("localhost", 20000)
        assert not node_handler.tcp_ready
        assert node_handler.node == "localhost"
