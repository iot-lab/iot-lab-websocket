"""iotlabwebsocket tcp client tests."""
# -*- coding: utf-8 -*-

import sys
import math

import mock

from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado import gen

from tornado.testing import AsyncTestCase, gen_test, bind_unused_port

from iotlabwebsocket.clients.tcp_client import (
    TCPClient,
    NODE_TCP_PORT,
    CHUNK_SIZE,
    MAX_BYTES_RECEIVED_PER_PERIOD,
)


class TCPServerStub(TCPServer):

    stream = None
    received = False

    @gen.coroutine
    def handle_stream(self, stream, address):
        self.stream = stream
        while True:
            try:
                yield self.stream.read_bytes(1)
                self.received = True
            except StreamClosedError:
                break


class NodeHandlerTest(AsyncTestCase):
    @gen_test
    def test_tcp_connection(self):
        client = TCPClient()

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        on_close = mock.Mock()
        on_data = mock.Mock()

        # Connect to the TCP server stub
        yield client.start("localhost", on_data, on_close)
        assert client.ready
        assert client.node == "localhost"

        # String is sent via websocket character by character
        message = b"Hello\nWorld"
        server.stream.write(message)
        yield gen.sleep(0.01)
        on_data.assert_called_once()
        on_data.assert_called_with("localhost", message)
        on_data.call_count = 0

        message = b"a" * CHUNK_SIZE
        server.stream.write(message)
        yield gen.sleep(0.01)
        on_data.assert_called_once()
        on_data.assert_called_with("localhost", message)
        on_data.call_count = 0

        message = b"a" * (CHUNK_SIZE + 1)
        server.stream.write(message)
        yield gen.sleep(0.01)
        assert on_data.call_count == 2
        on_data.call_count = 0

        # Raw bytes data are correctly sent to the connected websockets
        message = b"\xAA\xBB"
        server.stream.write(message)
        yield gen.sleep(0.01)
        assert on_data.call_count == 1
        on_data.assert_called_with("localhost", message)
        on_data.call_count = 0

        # Data sent by the node_handler should be received by the TCPServer:
        client.send(b"test")
        yield gen.sleep(0.01)
        on_data.call_count == 1
        assert server.received

        # Sending unicode character works
        on_data.call_count = 0
        server.received = False
        message = "éééààà°°°°"
        if sys.version_info[0] > 2:
            message = message.encode("utf-8")
        client.send(message)
        yield gen.sleep(0.01)
        on_data.call_count == 1
        assert server.received

        # Sending from the node handler without an opened connection has
        # has no effect
        server.received = False
        client.stop()
        yield gen.sleep(0.01)
        on_close.assert_called_once()
        client.send(b"test")
        yield gen.sleep(0.01)
        assert not server.received

        # When the TCP connection is lost, all websockets are closed
        yield client.start("localhost", on_data, on_close)
        assert client.ready
        assert client.node == "localhost"

        on_close.call_count = 0
        server.stream.close()
        yield gen.sleep(0.01)
        on_close.assert_called_once()
        assert not client.ready

    @gen_test
    def test_tcp_too_fast(self):
        client = TCPClient()

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        on_close = mock.Mock()
        on_data = mock.Mock()

        # Connect to the TCP server stub
        yield client.start("localhost", on_data, on_close)
        assert client.ready
        assert client.node == "localhost"

        # String is sent via websocket character by character
        message = b"A" * MAX_BYTES_RECEIVED_PER_PERIOD
        server.stream.write(message)
        yield gen.sleep(0.01)
        assert (
            on_data.call_count
            == (math.floor(MAX_BYTES_RECEIVED_PER_PERIOD / CHUNK_SIZE)) + 1
        )
        yield gen.sleep(1)
        server.stream.write(b"Too fast")
        yield gen.sleep(0.01)
        on_close.assert_called_once()

    @gen_test
    def test_tcp_failed_connection(self):
        client = TCPClient()
        on_close = mock.Mock()

        # Cannot connect because TCP server is not running
        yield client.start("localhost", None, on_close)
        assert not client.ready
        assert client.node == "localhost"
