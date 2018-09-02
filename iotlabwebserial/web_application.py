"""iotlabwebserial main web application."""

import argparse
import logging
from collections import defaultdict

import tornado

from .node_handler import NodeHandler
from .http_handler import HttpRequestHandler
from .websocket_handler import WebsocketClientHandler
from .helpers import start_application

LOGGER = logging.getLogger("iotlabwebserial")

NODE_TCP_PORT = 20000


class WebApplication(tornado.web.Application):
    """IoT-LAB websocket to tcp redirector."""

    def __init__(self, debug=False):
        if debug:
            LOGGER.setLevel(logging.DEBUG)

        handlers = [
            (r"/node/key", HttpRequestHandler),
            (r"/ws/localhost", WebsocketClientHandler, dict(node='localhost')),
        ]
        settings = {'debug': True}

        self.handlers = defaultdict(NodeHandler)

        super(WebApplication, self).__init__(handlers, **settings)

    def handle_websocket_validation(self, websocket):
        """Handle the websocket connection once authentified."""
        node = websocket.node
        handler = self.handlers[node]
        if not handler.websockets:
            # Open the tcp connection on first websocket connection.
            handler.start_tcp_connection(node, NODE_TCP_PORT)
        handler.websockets.append(websocket)

    def handle_websocket_message(self, websocket, message):
        """Handle a message coming from a websocket."""
        handler = self.handlers[websocket.node]
        if handler.tcp_ready:
            handler.tcp.write(message.encode())
        else:
            LOGGER.debug("No TCP connection opened, skipping message")
            websocket.write_message("No TCP connection opened, cannot send "
                                    "message '{}'.\n".format(message))

    def handle_websocket_close(self, websocket):
        """Handle the disconnection of a websocket."""
        handler = self.handlers[websocket.node]
        handler.websockets.remove(websocket)

        # websockets list is now empty for given node, closing tcp connection.
        if handler.tcp_ready and not handler.websockets:
            LOGGER.debug("Closing TCP connection to node '%s'", websocket.node)
            handler.tcp.close()
            del handler

    def handle_http_post(self, node, key):
        """Handle an HTTP POST request."""
        self.handlers[node].key = key


def parse_command_line():
    """Parse the command line of the web application."""
    parser = argparse.ArgumentParser(description="Test Websocket node")
    parser.add_argument('--port', type=str, default="8000",
                        help="Listening port")
    parser.add_argument('--debug', action='store_true',
                        help="Enable debug mode")
    args = parser.parse_args()
    return args


def main():
    """Main function of the web application."""
    args = parse_command_line()
    start_application(WebApplication(debug=args.debug), args.port)

    tornado.ioloop.IOLoop.current().start()
