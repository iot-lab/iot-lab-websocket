"""iotlabwebsocket tcp client tests."""

import asyncio
import math

import mock
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.testing import AsyncTestCase, bind_unused_port, gen_test

from iotlabwebsocket.clients.tcp_client import (
    CHUNK_SIZE,
    MAX_BYTES_RECEIVED_PER_PERIOD,
    NODE_TCP_PORT,
    TCPClient,
)


class TCPServerStub(TCPServer):
    stream = None
    received = False

    async def handle_stream(self, stream, address):
        self.stream = stream
        while True:
            try:
                await self.stream.read_bytes(1)
                self.received = True
            except StreamClosedError:
                break


class NodeHandlerTest(AsyncTestCase):
    @gen_test
    async def test_tcp_connection(self):
        client = TCPClient()

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        on_close = mock.Mock()
        on_data = mock.Mock()

        # Connect to the TCP server stub
        await client.start("localhost", on_data, on_close)
        assert client.ready
        assert client.node == "localhost"

        # String is sent via websocket character by character
        message = b"Hello\nWorld"
        server.stream.write(message)
        await asyncio.sleep(0.01)
        on_data.assert_called_once()
        on_data.assert_called_with("localhost", message)
        on_data.call_count = 0

        message = b"a" * CHUNK_SIZE
        server.stream.write(message)
        await asyncio.sleep(0.01)
        on_data.assert_called_once()
        on_data.assert_called_with("localhost", message)
        on_data.call_count = 0

        message = b"a" * (CHUNK_SIZE + 1)
        server.stream.write(message)
        await asyncio.sleep(0.01)
        assert on_data.call_count == 2
        on_data.call_count = 0

        # Raw bytes data are correctly sent to the connected websockets
        message = b"\xaa\xbb"
        server.stream.write(message)
        await asyncio.sleep(0.01)
        assert on_data.call_count == 1
        on_data.assert_called_with("localhost", message)
        on_data.call_count = 0

        # Data sent by the node_handler should be received by the TCPServer:
        client.send(b"test")
        await asyncio.sleep(0.01)
        assert server.received

        # Sending unicode character works
        server.received = False
        message = "éééààà°°°°".encode("utf-8")
        client.send(message)
        await asyncio.sleep(0.01)
        assert server.received

        # Sending from the node handler without an opened connection has
        # has no effect
        server.received = False
        client.stop()
        await asyncio.sleep(0.01)
        on_close.assert_called_once()
        client.send(b"test")
        await asyncio.sleep(0.01)
        assert not server.received

        # When the TCP connection is lost, all websockets are closed
        await client.start("localhost", on_data, on_close)
        assert client.ready
        assert client.node == "localhost"

        on_close.call_count = 0
        server.stream.close()
        await asyncio.sleep(0.01)
        on_close.assert_called_once()
        assert not client.ready

    @gen_test
    async def test_tcp_too_fast(self):
        client = TCPClient()

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        on_close = mock.Mock()
        on_data = mock.Mock()

        # Connect to the TCP server stub
        await client.start("localhost", on_data, on_close)
        assert client.ready
        assert client.node == "localhost"

        # String is sent via websocket character by character
        message = b"A" * MAX_BYTES_RECEIVED_PER_PERIOD
        server.stream.write(message)
        await asyncio.sleep(0.01)
        assert (
            on_data.call_count
            == (math.floor(MAX_BYTES_RECEIVED_PER_PERIOD / CHUNK_SIZE)) + 1
        )
        await asyncio.sleep(1)
        server.stream.write(b"Too fast")
        await asyncio.sleep(0.01)
        on_close.assert_called_once()

    @gen_test
    async def test_tcp_period_reset(self):
        client = TCPClient()
        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        on_close = mock.Mock()
        on_data = mock.Mock()

        call_count = [0]

        def _time():
            call_count[0] += 1
            return 0 if call_count[0] <= 2 else 2

        with mock.patch(
            "iotlabwebsocket.clients.tcp_client.time"
        ) as mock_time:
            mock_time.time.side_effect = _time
            await client.start("localhost", on_data, on_close)
            assert client.ready

            server.stream.write(b"hello")
            await asyncio.sleep(0.01)

            # Second write triggers the period-elapsed branch (time returns 2),
            # bytes are within limit so received_bytes resets (lines 87-88).
            server.stream.write(b"world")
            await asyncio.sleep(0.01)

            client.stop()
            await asyncio.sleep(0.01)

        on_close.assert_called_once()
        assert on_data.call_count >= 2

    @gen_test
    async def test_tcp_failed_connection(self):
        client = TCPClient()
        on_close = mock.Mock()

        # Cannot connect because TCP server is not running
        await client.start("localhost", None, on_close)
        assert not client.ready
        assert client.node == "localhost"
