"""iotlabwebserial main web application."""

from collections import defaultdict

import tornado

from tornado import gen

from . import DEFAULT_API_HOST
from .logger import LOGGER
from .clients.ssh_client import SSHClient
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
             WebsocketClientHandler, dict(api=api)),
            (r"/ws/[a-z]+/[0-9]+/[a-z0-9]+-?[a-z0-9]*-?[0-9]*/ssh",
             WebsocketClientHandler, dict(api=api))
        ]

        if use_local_api:
            api.protocol = 'http'
            api.host = DEFAULT_API_HOST
            handlers.append((r"/api/experiments/[0-9]+/.*",
                             HttpApiRequestHandler, dict(token=token)))

        self.tcp_clients = defaultdict(TCPClient)
        self.serial_websockets = defaultdict(list)
        self.user_connections = defaultdict(int)

        self.ssh_websockets = {}

        super(WebApplication, self).__init__(handlers, **settings)

    def _websocket_serial_open(self, websocket, user, site, node):
        tcp_client = self.tcp_clients[node]
        if not self.serial_websockets[node]:
            # Open the tcp connection on first websocket connection.
            tcp_client.start(node, on_data=self.handle_tcp_data,
                             on_close=self.handle_tcp_close)
        if len(self.serial_websockets[node]) == MAX_WEBSOCKETS_PER_NODE:
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
            self.serial_websockets[node].append(websocket)

    @gen.coroutine
    def _websocket_ssh_open(self, websocket, user, site, node):
        ssh_client = SSHClient(node, on_data=self.handle_ssh_data,
                               on_close=self.handle_ssh_close)
        started = yield ssh_client.start()
        if not started:
            websocket.close(code=1001,
                            reason="Cannot connect to node{}".format(node))
            return
        if self.user_connections[user] == MAX_WEBSOCKETS_PER_USER:
            websocket.close(
                code=1000,
                reason=("Max number of connections ({}) reached for user {} "
                        "on site {}."
                        .format(MAX_WEBSOCKETS_PER_USER, user, site)))
        else:
            self.user_connections[user] += 1
            self.ssh_websockets[ssh_client] = websocket

    def handle_websocket_open(self, websocket, client_type='serial'):
        """Handle the websocket connection once authentified."""
        node = websocket.node
        user = websocket.user
        site = websocket.site
        if client_type == "serial":
            self._websocket_serial_open(websocket, user, site, node)
        elif client_type == "ssh":
            self._websocket_ssh_open(websocket, user, site, node)
        else:
            LOGGER.debug("Invalid client type '%s'", client_type)

    def _websocket_serial_data(self, websocket, data):
        tcp_client = self.tcp_clients[websocket.node]
        if tcp_client.ready:
            tcp_client.send(data.encode())
        else:
            LOGGER.debug("No TCP connection opened, skipping message")
            websocket.write_message("No TCP connection opened, cannot send "
                                    "message '{}'.\n".format(data))

    def _websocket_ssh_data(self, websocket, data):
        for client, websocket_value in self.ssh_websockets.items():
            if websocket_value is websocket:
                ssh_client = client
        if ssh_client.ready:
            ssh_client.send(data.encode())
        else:
            LOGGER.debug("No SSH connection opened, skipping message")
            websocket.write_message("No SSH connection opened, cannot send "
                                    "message '{}'.\n".format(data))

    def handle_websocket_data(self, websocket, data, client_type='serial'):
        """Handle a message coming from a websocket."""
        if client_type == "serial":
            self._websocket_serial_data(websocket, data)
        elif client_type == "ssh":
            self._websocket_ssh_data(websocket, data)
        else:
            LOGGER.debug("Invalid client type '%s'", client_type)

    def _websocket_serial_close(self, websocket, node):
        tcp_client = self.tcp_clients[node]
        if websocket in self.serial_websockets[node]:
            self.serial_websockets[node].remove(websocket)

        # websockets list is now empty for given node, closing tcp connection.
        if tcp_client.ready and not self.serial_websockets[node]:
            LOGGER.debug("Closing TCP connection to node '%s'", node)
            tcp_client.stop()
            self.tcp_clients.pop(node)
            del tcp_client

    def _websocket_ssh_close(self, websocket, node):
        ssh_client = None
        for client, websocket_value in self.ssh_websockets.items():
            if websocket_value is websocket:
                ssh_client = client
                if ssh_client.ready:
                    LOGGER.debug("Closing SSH connection to node '%s'", node)
                    ssh_client.stop()
        if ssh_client in self.ssh_websockets:
            self.ssh_websockets.pop(ssh_client)

    def handle_websocket_close(self, websocket, client_type='serial'):
        """Handle the disconnection of a websocket."""
        node = websocket.node
        user = websocket.user
        if client_type == "serial":
            self._websocket_serial_close(websocket, node)
        elif client_type == "ssh":
            self._websocket_ssh_close(websocket, node)
        else:
            LOGGER.debug("Invalid client type '%s'", client_type)

        if self.user_connections[user] > 0:
            self.user_connections[user] -= 1

    def handle_tcp_data(self, node, data):
        """Forwards data from TCP connection to all websocket clients."""
        for websocket in self.serial_websockets[node]:
            websocket.write_message(data)

    def handle_tcp_close(self, node, reason="Cannot connect"):
        """Close all websockets connected to a node when TCP is closed."""
        for websocket in self.serial_websockets[node]:
            websocket.close(code=1000, reason=reason)

    @gen.coroutine
    def handle_ssh_data(self, client, data):
        """Forwards data from SSH connection to the attached websocket."""
        self.ssh_websockets[client].write_message(data)

    def handle_ssh_close(self, client):
        """Close the websocket connected when the attached SSH is closed."""
        self.ssh_websockets[client].close(
            code=1000, reason="Connection to {} is closed".format(client.host))

    def stop(self):
        # pylint:disable=undefined-loop-variable
        """Stop any pending websocket connection."""
        reason = "server is restarting"
        code = 1001
        for websockets in self.serial_websockets.values():
            for websocket in websockets:
                websocket.close(code=code, reason=reason)

        for websockets in self.ssh_websockets.values():
            websocket.close(code=code, reason=reason)
