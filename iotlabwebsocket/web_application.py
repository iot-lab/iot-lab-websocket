"""iotlabwebserial main web application."""

from collections import defaultdict

import tornado

from . import DEFAULT_API_HOST
from .logger import LOGGER
from .clients.tcp_client import TCPClient
from .handlers.http_handler import HttpApiRequestHandler
from .handlers.websocket_handler import WebsocketClientHandler

MAX_WEBSOCKETS_PER_NODE = 2
MAX_WEBSOCKETS_PER_USER = 10


class WebApplication(tornado.web.Application):
    """IoT-LAB websocket to tcp redirector."""

    def __init__(self, api, use_local_api=False, token=''):
        settings = {'debug': True}
        handlers = [
            (r"/ws/[a-z]+/[0-9]+/[a-z0-9]+-?[a-z0-9]*-?[0-9]*/serial",
             WebsocketClientHandler, dict(api=api))
        ]

        if use_local_api:
            api.protocol = 'http'
            api.host = DEFAULT_API_HOST
            handlers.append((r"/api/experiments/[0-9]+/.*",
                             HttpApiRequestHandler, dict(token=token)))

        self.tcp_clients = defaultdict(TCPClient)
        self.websockets = defaultdict(list)
        self.user_connections = defaultdict(int)

        super(WebApplication, self).__init__(handlers, **settings)

    def handle_websocket_open(self, websocket):
        """Handle the websocket connection once authentified."""
        node = websocket.node
        user = websocket.user
        site = websocket.site
        tcp_client = self.tcp_clients[node]
        if not self.websockets[node]:
            # Open the tcp connection on first websocket connection.
            tcp_client.start(node, on_data=self.handle_tcp_data,
                             on_close=self.handle_tcp_close)
        if len(self.websockets[node]) == MAX_WEBSOCKETS_PER_NODE:
            websocket.close(
                code=1000,
                reason=("Cannot open more than {} connections to node {}."
                        .format(MAX_WEBSOCKETS_PER_NODE, node)))
        elif self.user_connections[user] == MAX_WEBSOCKETS_PER_USER:
            websocket.close(
                code=1000,
                reason=("Max number of connections ({}) reached for user {} "
                        "on site {}."
                        .format(MAX_WEBSOCKETS_PER_USER, user, site)))
        else:
            self.user_connections[user] += 1
            self.websockets[node].append(websocket)

    def handle_websocket_data(self, websocket, data):
        """Handle a message coming from a websocket."""
        tcp_client = self.tcp_clients[websocket.node]
        if tcp_client.ready:
            tcp_client.send(data.encode())
        else:
            LOGGER.debug("No TCP connection opened, skipping message")
            websocket.write_message("No TCP connection opened, cannot send "
                                    "message '{}'.\n".format(data))

    def handle_websocket_close(self, websocket):
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
            LOGGER.debug("Closing TCP connection to node '%s'", node)
            tcp_client.stop()
            self.tcp_clients.pop(node)
            del tcp_client

    def handle_tcp_data(self, node, data):
        """Forwards data from TCP connection to all websocket clients."""
        for websocket in self.websockets[node]:
            websocket.write_message(data)

    def handle_tcp_close(self, node, reason="Cannot connect"):
        """Close all websockets connected to a node when TCP is closed."""
        for websocket in self.websockets[node]:
            websocket.close(code=1000, reason=reason)

    def stop(self):
        """Stop any pending websocket connection."""
        for websockets in self.websockets.values():
            for websocket in websockets:
                websocket.close(code=1001, reason="server is restarting")
