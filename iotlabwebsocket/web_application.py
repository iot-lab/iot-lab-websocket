"""iotlabwebserial main web application."""

from collections import defaultdict

import tornado

from . import DEFAULT_AUTH_HOST
from .logger import LOGGER
from .clients.tcp_client import TCPClient
from .handlers.http_handler import HttpAuthRequestHandler
from .handlers.websocket_handler import WebsocketClientHandler

AUTH_URL = "http://{}:{}/experiments"


class WebApplication(tornado.web.Application):
    """IoT-LAB websocket to tcp redirector."""

    def __init__(self, auth_host, auth_port, use_local_auth=False, token=''):
        auth_url = AUTH_URL.format(auth_host, auth_port)
        settings = {'debug': True}
        handlers = [
            (r"/ws/[0-9]+/.*/serial", WebsocketClientHandler,
             dict(auth_url=auth_url))
        ]

        if auth_host == DEFAULT_AUTH_HOST and use_local_auth:
            handlers.append((r"/experiments/[0-9]+/token",
                             HttpAuthRequestHandler, dict(token=token)))

        self.tcp_clients = defaultdict(TCPClient)
        self.websockets = defaultdict(list)

        super(WebApplication, self).__init__(handlers, **settings)

    def handle_websocket_open(self, websocket):
        """Handle the websocket connection once authentified."""
        node = websocket.node
        tcp_client = self.tcp_clients[node]
        if not self.websockets[node]:
            # Open the tcp connection on first websocket connection.
            tcp_client.start(node, on_data=self.handle_tcp_data,
                             on_close=self.handle_tcp_close)
        self.websockets[node].append(websocket)

    def handle_websocket_data(self, websocket, data):
        """Handle a message coming from a websocket."""
        tcp_client = self.tcp_clients[websocket.node]
        if tcp_client.ready:
            tcp_client.send(data.encode())
        else:
            LOGGER.debug("No TCP connection opened, skipping message")
            websocket.write_data("No TCP connection opened, cannot send "
                                 "message '{}'.\n".format(data))

    def handle_websocket_close(self, websocket):
        """Handle the disconnection of a websocket."""
        node = websocket.node
        tcp_client = self.tcp_clients[node]
        self.websockets[node].remove(websocket)

        # websockets list is now empty for given node, closing tcp connection.
        if tcp_client.ready and not self.websockets[node]:
            LOGGER.debug("Closing TCP connection to node '%s'", node)
            tcp_client.stop()
            del tcp_client

    def handle_tcp_data(self, node, data):
        """Forwards data from TCP connection to all websocket clients."""
        for websocket in self.websockets[node]:
            websocket.write_message(data)

    def handle_tcp_close(self, node):
        """Close all websockets connected to a node when TCP is closed."""
        for websocket in self.websockets[node]:
            websocket.close()

    def stop(self):
        """Stop any pending websocket connection."""
        for websockets in self.websockets.values():
            for websocket in websockets:
                websocket.close()
