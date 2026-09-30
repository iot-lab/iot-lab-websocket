"""iotlabwebsocket web application tests."""

import asyncio
import json

import mock
import tornado
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.testing import AsyncHTTPTestCase, bind_unused_port, gen_test
from tornado.websocket import WebSocketClosedError

from iotlabwebsocket.api import ApiClient
from iotlabwebsocket.clients.tcp_client import NODE_TCP_PORT
from iotlabwebsocket.web_application import (
    MAX_WEBSOCKETS_PER_NODE,
    MAX_WEBSOCKETS_PER_USER,
    WebApplication,
)


class TCPServerStub(TCPServer):
    stream = None

    async def handle_stream(self, stream, address):
        self.stream = stream
        while True:
            try:
                await self.stream.read_bytes(1)
            except StreamClosedError:
                break


class TestWebApplication(AsyncHTTPTestCase):
    def get_app(self):
        self.application = WebApplication(
            self.api, use_local_api=True, token="token"
        )
        return self.application

    def setUp(self):
        self.api = ApiClient("http")
        super().setUp()
        self.api.port = self.get_http_port()

        assert len(self.application.websockets) == 0

    @mock.patch("iotlabwebsocket.clients.tcp_client.TCPClient.send")
    @mock.patch("iotlabwebsocket.clients.tcp_client.TCPClient.stop")
    @mock.patch("iotlabwebsocket.clients.tcp_client.TCPClient.start")
    @mock.patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    async def test_tcp_connections_unit(self, nodes, start, stop, send):
        url = f"ws://localhost:{self.api.port}/ws/local/123/node-1/serial/raw"
        nodes.return_value = json.dumps({"nodes": ["node-1.local"]})

        websocket = await tornado.websocket.websocket_connect(
            url, subprotocols=["user", "token", "token"]
        )

        assert len(self.application.websockets["node-1"]) == 1
        assert self.application.websockets["node-1"][0].user == "user"
        assert self.application.websockets["node-1"][0].node == "node-1"

        start.assert_called_once()
        args, kwargs = start.call_args

        assert len(args) == 1
        assert args[0] == "node-1"
        assert kwargs == {
            "on_data": self.application.handle_tcp_data,
            "on_close": self.application.handle_tcp_close,
        }

        # Forcing TCP client to be ready, just for the test
        self.application.tcp_clients["node-1"].ready = True

        # another websocket connection for the same node doesn't start a new
        # TCP connection
        start.call_count = 0
        websocket2 = await tornado.websocket.websocket_connect(
            url, subprotocols=["user", "token", "token"]
        )

        assert start.call_count == 0
        assert len(self.application.websockets["node-1"]) == 2
        for ws in self.application.websockets["node-1"]:
            assert ws.user == "user"
            assert ws.node == "node-1"

        websocket2.close(code=1234, reason="test reason")
        await asyncio.sleep(0.1)

        # There's still a websocket connection opened, so TCP client is not
        # closed
        assert stop.call_count == 0
        assert len(self.application.websockets["node-1"]) == 1

        # Send some data
        websocket.write_message(b"test", binary=True)
        await asyncio.sleep(0.1)

        send.assert_called_once()
        send.assert_called_with(b"test")

        # Close last websocket
        websocket.close(code=5678, reason="Big Test")
        await asyncio.sleep(0.1)

        assert stop.call_count == 1
        assert len(self.application.websockets["node-1"]) == 0
        assert "node-1" not in self.application.tcp_clients

    @mock.patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    async def test_tcp_connection_server(self, nodes):
        url = (
            f"ws://localhost:{self.api.port}/ws/local/123/localhost/serial/raw"
        )
        nodes.return_value = json.dumps({"nodes": ["localhost.local"]})

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        websocket = await tornado.websocket.websocket_connect(
            url, subprotocols=["user", "token", "token"]
        )

        assert len(self.application.websockets["localhost"]) == 1

        # Leave some time for the TCP connection to be ready
        await asyncio.sleep(0.1)
        assert self.application.tcp_clients["localhost"].ready

        # Send some data
        websocket_srv = self.application.websockets["localhost"][0]
        websocket_srv.write_message = mock.Mock()
        message = "test°°°ééààà".encode("utf-8")
        await server.stream.write(message)

        await asyncio.sleep(0.1)
        assert websocket_srv.write_message.call_count == 1
        websocket_srv.write_message.call_count = 0

        # Smoke test to check that the websocket gets a message when the TCP
        # connection is not opened yet
        self.application.tcp_clients["localhost"].ready = False
        websocket.write_message(b"test", binary=True)
        await asyncio.sleep(0.1)
        websocket_srv.write_message.assert_called_with(
            "No TCP connection opened, cannot send message 'test'.\n"
        )
        self.application.tcp_clients["localhost-1"].ready = True

        # Force close from TCP server, all websockets should be closed
        # automatically and TCP client connection as well
        server.stream.close()
        await asyncio.sleep(0.1)

        assert not self.application.tcp_clients["localhost"].ready
        assert len(self.application.websockets["node-1"]) == 0

    @mock.patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    async def test_tcp_connection_server_text(self, nodes):
        url = f"ws://localhost:{self.api.port}/ws/local/123/localhost/serial"
        nodes.return_value = json.dumps({"nodes": ["localhost.local"]})

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        _ = await tornado.websocket.websocket_connect(
            url, subprotocols=["user", "token", "token"]
        )

        assert len(self.application.websockets["localhost"]) == 1

        # Leave some time for the TCP connection to be ready
        await asyncio.sleep(0.1)
        assert self.application.tcp_clients["localhost"].ready

        # Send some data
        websocket_srv = self.application.websockets["localhost"][0]
        websocket_srv.write_message = mock.Mock()
        message = "test".encode("utf-8")
        await server.stream.write(message)

        await asyncio.sleep(0.1)
        assert websocket_srv.write_message.call_count == 1

        # Send some pure binary data
        websocket_srv.write_message.call_count = 0
        websocket_srv = self.application.websockets["localhost"][0]
        websocket_srv.write_message = mock.Mock()
        message = b"\xaa\xbb\xcc\xff"
        await server.stream.write(message)

        await asyncio.sleep(0.1)
        assert websocket_srv.write_message.call_count == 0

    @mock.patch("iotlabwebsocket.handlers.http_handler._nodes")
    @gen_test
    async def test_application_stop(self, nodes):
        url = (
            f"ws://localhost:{self.api.port}/ws/local/123/localhost/serial/raw"
        )
        nodes.return_value = json.dumps({"nodes": ["localhost.local"]})

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        for _ in range(10):
            _ = await tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "token"]
            )

        assert (
            len(self.application.websockets["localhost"])
            == MAX_WEBSOCKETS_PER_NODE
        )

        self.application.stop()
        await asyncio.sleep(0.1)
        assert len(self.application.websockets["localhost"]) == 0

    @mock.patch("iotlabwebsocket.web_application.MAX_WEBSOCKETS_PER_NODE", 20)
    @gen_test
    async def test_user_max_connections(self):
        url = "ws://localhost:{}/ws/local/123/localhost/serial/raw".format(
            self.api.port
        )

        sock, _ = bind_unused_port()
        server = TCPServerStub()
        server.add_socket(sock)
        server.listen(NODE_TCP_PORT)

        for _i in range(MAX_WEBSOCKETS_PER_USER + 10):
            _ = await tornado.websocket.websocket_connect(
                url, subprotocols=["user", "token", "token"]
            )

        assert (
            self.application.user_connections["user"]
            == MAX_WEBSOCKETS_PER_USER
        )

        i = 1
        for websockets in self.application.websockets.values():
            websockets[0].close(code=1234, reason="Too many connections test")
            await asyncio.sleep(0.1)
            assert (
                self.application.user_connections["user"]
                == MAX_WEBSOCKETS_PER_USER - i
            )
            i += 1

    def test_tcp_data_skips_closed_websocket(self):
        closing = mock.Mock(text=False)
        closing.write_message.side_effect = WebSocketClosedError()
        other = mock.Mock(text=False)
        self.application.websockets["node-1"] = [closing, other]

        # A websocket closing does not prevent the others from receiving data
        self.application.handle_tcp_data("node-1", b"data")

        other.write_message.assert_called_once_with(b"data", binary=True)

    @mock.patch(
        "iotlabwebsocket.clients.tcp_client.TCPClient.start",
        new_callable=mock.AsyncMock,
    )
    @gen_test
    async def test_rejected_websocket_keeps_user_count(self, start):
        websockets = [
            mock.Mock(node="node-1", user="user", site="local")
            for _ in range(MAX_WEBSOCKETS_PER_NODE + 1)
        ]
        for websocket in websockets:
            self.application.handle_websocket_open(websocket)
        await asyncio.sleep(0)

        # The last one is rejected by the per node limit
        websockets[-1].close.assert_called_once()
        assert (
            self.application.user_connections["user"]
            == MAX_WEBSOCKETS_PER_NODE
        )

        # Tornado calls on_close for the rejected websocket too
        self.application.handle_websocket_close(websockets[-1])
        assert (
            self.application.user_connections["user"]
            == MAX_WEBSOCKETS_PER_NODE
        )

    @mock.patch("iotlabwebsocket.clients.tcp_client.TCPClient.stop")
    @mock.patch(
        "iotlabwebsocket.clients.tcp_client.TCPClient.start",
        new_callable=mock.AsyncMock,
    )
    @gen_test
    async def test_close_while_tcp_connecting(self, start, stop):
        websocket = mock.Mock(node="node-1", user="user", site="local")
        self.application.handle_websocket_open(websocket)
        await asyncio.sleep(0)
        assert not self.application.tcp_clients["node-1"].ready

        # Last websocket closed before the TCP connection is ready
        self.application.handle_websocket_close(websocket)
        stop.assert_called_once()
        assert "node-1" not in self.application.tcp_clients

    def test_tcp_data_text_split_character(self):
        websocket = mock.Mock(text=True)
        self.application.websockets["node-1"] = [websocket]
        data = "é°".encode("utf-8")

        # Chunk boundaries fall in the middle of each character
        self.application.handle_tcp_data("node-1", data[:1])
        self.application.handle_tcp_data("node-1", data[1:3])
        self.application.handle_tcp_data("node-1", data[3:])

        assert websocket.write_message.call_args_list == [
            mock.call("é"),
            mock.call("°"),
        ]

        # Undecodable data is skipped without affecting the next chunks
        websocket.write_message.reset_mock()
        self.application.handle_tcp_data("node-1", b"\xff")
        self.application.handle_tcp_data("node-1", b"ok")
        websocket.write_message.assert_called_once_with("ok")

    def test_websocket_binary_data_without_tcp(self):
        websocket = mock.Mock(node="node-1", text=False)

        # Binary data sent by a raw websocket before the TCP connection is
        # ready is reported, not raised
        self.application.handle_websocket_data(websocket, b"\xff")

        websocket.write_message.assert_called_once_with(
            "No TCP connection opened, cannot send message '\ufffd'.\n"
        )
