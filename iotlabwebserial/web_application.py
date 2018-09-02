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

    def handle_websocket_validation(self, ws):
        handler = self.handlers[ws.node]
        if not handler.websockets:
            # Open the tcp connection on first websocket connection.
            handler.start_tcp_connection(ws.node, NODE_TCP_PORT)
        handler.websockets.append(ws)

    def handle_websocket_message(self, ws, message):
        handler = self.handlers[ws.node]
        if handler.tcp_ready:
            handler.tcp.write(message.encode())
        else:
            LOGGER.debug("No TCP connection opened, skipping message")
            ws.write_message("No TCP connection opened, cannot send "
                             "message '{}'.\n".format(message))

    def handle_websocket_close(self, ws):
        handler = self.handlers[ws.node]
        handler.websockets.remove(ws)

        # websockets list is now empty for given node, closing tcp connection.
        if handler.tcp_ready and not handler.websockets:
            LOGGER.debug("Closing TCP connection to node '%s'", ws.node)
            handler.tcp.close()
            del handler

    def handle_http_post(self, node, key):
        self.handlers[node].key = key


def parse_command_line():
    parser = argparse.ArgumentParser(description="Test Websocket node")
    parser.add_argument('--port', type=str, default="8000",
                        help="Listening port")
    parser.add_argument('--debug', action='store_true',
                        help="Enable debug mode")
    args = parser.parse_args()
    return args


def main():
    args = parse_command_line()
    start_application(WebApplication(debug=args.debug), args.port)

    tornado.ioloop.IOLoop.current().start()
