"""iotlabwebserial main web application."""

import asyncio
from collections import defaultdict

import tornado

from . import DEFAULT_API_HOST
from .api import ApiClient
from .clients.tcp_client import TCPClient
from .handlers.http_handler import HttpApiRequestHandler
from .handlers.websocket_handler import WebsocketClientHandler
from .logger import LOGGER

MAX_WEBSOCKETS_PER_NODE = 2
MAX_WEBSOCKETS_PER_USER = 10


class WebApplication(tornado.web.Application):
    """IoT-LAB websocket to tcp redirector."""

    def __init__(
        self,
        api: ApiClient,
        use_local_api: bool = False,
        token: str = "",
        debug: bool = False,
    ) -> None:
        handlers = [
            (
                r"/ws/[a-z0-9\-_]+/[0-9]+/[a-z0-9]+-?[a-z0-9]*-?[0-9]*/serial",
                WebsocketClientHandler,
                {"api": api, "text": True},
            ),
            (
                r"/ws/[a-z0-9\-_]+/[0-9]+/[a-z0-9]+-?[a-z0-9]*-?[0-9]*/serial/raw",
                WebsocketClientHandler,
                {"api": api, "text": False},
            ),
        ]

        if use_local_api:
            api.protocol = "http"
            api.host = DEFAULT_API_HOST
            handlers.append(
                (
                    r"/api/experiments/[0-9]+/.*",
                    HttpApiRequestHandler,
                    {"token": token},
                )
            )

        self.tcp_clients = defaultdict(TCPClient)
        self.websockets = defaultdict(list)
        self.user_connections = defaultdict(int)

        super().__init__(handlers, debug=debug)

    def handle_websocket_open(self, websocket: WebsocketClientHandler) -> None:
        """Handle the websocket connection once authentified."""
        node = websocket.node
        user = websocket.user
        site = websocket.site

        if len(self.websockets[node]) == MAX_WEBSOCKETS_PER_NODE:
            websocket.close(
                code=1000,
                reason=(
                    f"Cannot open more than {MAX_WEBSOCKETS_PER_NODE} "
                    f"connections to node {node}."
                ),
            )
            return

        if self.user_connections[user] == MAX_WEBSOCKETS_PER_USER:
            websocket.close(
                code=1000,
                reason=(
                    f"Max number of connections ({MAX_WEBSOCKETS_PER_USER}) "
                    f"reached for user {user} on site {site}."
                ),
            )
            return

        self.user_connections[user] += 1
        self.websockets[node].append(websocket)

        if len(self.websockets[node]) == 1:
            # First websocket for this node: open the TCP connection.
            asyncio.ensure_future(
                self.tcp_clients[node].start(
                    node,
                    on_data=self.handle_tcp_data,
                    on_close=self.handle_tcp_close,
                )
            )

    def handle_websocket_data(
        self, websocket: WebsocketClientHandler, data: bytes
    ) -> None:
        """Handle a message coming from a websocket."""
        tcp_client = self.tcp_clients[websocket.node]
        if tcp_client.ready:
            tcp_client.send(data)
        else:
            LOGGER.debug("No TCP connection opened, skipping message")
            websocket.write_message(
                f"No TCP connection opened, cannot send "
                f"message '{data.decode('utf-8')}'.\n"
            )

    def handle_websocket_close(
        self, websocket: WebsocketClientHandler
    ) -> None:
        """Handle the disconnection of a websocket."""
        node = websocket.node
        user = websocket.user
        tcp_client = self.tcp_clients[node]
        if websocket in self.websockets[node]:
            self.websockets[node].remove(websocket)
        if self.user_connections[user] > 0:
            self.user_connections[user] -= 1

        # websockets list is now empty for given node, closing tcp connection.
        if tcp_client.ready and not self.websockets[node]:
            LOGGER.debug(f"Closing TCP connection to node '{node}'")
            tcp_client.stop()
            self.tcp_clients.pop(node)

    def handle_tcp_data(self, node: str, data: bytes) -> None:
        """Forwards data from TCP connection to all websocket clients."""
        for websocket in self.websockets[node]:
            if websocket.text:
                try:
                    message = data.decode("utf-8")
                except UnicodeDecodeError:
                    LOGGER.debug(f"Cannot decode message: {data}")
                    continue
                websocket.write_message(message)
            else:
                websocket.write_message(data, binary=True)

    def handle_tcp_close(
        self, node: str, reason: str = "Cannot connect"
    ) -> None:
        """Close all websockets connected to a node when TCP is closed."""
        for websocket in self.websockets[node]:
            websocket.close(code=1000, reason=reason)

    def stop(self) -> None:
        """Stop any pending websocket connection."""
        for websockets in self.websockets.values():
            for websocket in websockets:
                websocket.close(code=1001, reason="server is restarting")
