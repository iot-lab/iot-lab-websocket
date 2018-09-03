"""iotlabwebserial main web application."""

import logging
from collections import defaultdict

import tornado

from .node_handler import NodeHandler
from .http_handler import HttpRequestHandler
from .websocket_handler import WebsocketClientHandler

LOGGER = logging.getLogger("iotlabwebserial")

NODE_TCP_PORT = 20000


class WebApplication(tornado.web.Application):
    """IoT-LAB websocket to tcp redirector."""

    def __init__(self, known_nodes):
        settings = {'debug': True}
        handlers = [
            (r"/experiment/start", HttpRequestHandler),
            (r"/experiment/stop", HttpRequestHandler),
        ]
        for node in known_nodes:
            LOGGER.debug("Add websocket handler for node '%s'", node)
            handlers += (r"/ws/{}".format(node), WebsocketClientHandler,
                         dict(node=node)),

        self.handlers = defaultdict(NodeHandler)
        self.experiments = defaultdict(list)

        super(WebApplication, self).__init__(handlers, **settings)

    def handle_websocket_validation(self, websocket):
        """Handle the websocket connection once authentified."""
        node = websocket.node
        handler = self.handlers[node]
        if not handler.websockets:
            # Open the tcp connection on first websocket connection.
            handler.start(node, NODE_TCP_PORT)
        handler.websockets.append(websocket)

    def handle_websocket_data(self, websocket, data):
        """Handle a message coming from a websocket."""
        handler = self.handlers[websocket.node]
        if handler.tcp_ready:
            handler.send(data.encode())
        else:
            LOGGER.debug("No TCP connection opened, skipping message")
            websocket.write_data("No TCP connection opened, cannot send "
                                 "message '{}'.\n".format(data))

    def handle_websocket_close(self, websocket):
        """Handle the disconnection of a websocket."""
        handler = self.handlers[websocket.node]
        handler.websockets.remove(websocket)

        # websockets list is now empty for given node, closing tcp connection.
        if handler.tcp_ready and not handler.websockets:
            LOGGER.debug("Closing TCP connection to node '%s'", websocket.node)
            handler.stop()
            del handler

    def handle_start_experiment(self, experiment_id, nodes, key):
        """Handle an HTTP POST request."""
        LOGGER.debug("Handle start experiment ('%s')", experiment_id)
        self.experiments[experiment_id] = nodes
        for node in nodes:
            self.handlers[node].key = key

    def handle_stop_experiment(self, experiment_id):
        """Handle an HTTP POST request."""
        LOGGER.debug("Handle stop experiment ('%s')", experiment_id)
        nodes = self.experiments[experiment_id]
        for node in nodes:
            self.handlers[node].stop()
            del self.handlers[node]
        del self.experiments[experiment_id]
