"""Websocket client"""

import sys
import logging

import tornado
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.websocket import websocket_connect, WebSocketClosedError
from tornado.httpclient import HTTPClientError

LOGGER = logging.getLogger("iotlabwebsocket")


class WebsocketClient(object):
    # pylint:disable=too-few-public-methods
    """Class that connects to a websocket server while listening to stdin."""

    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.websocket = None

    @gen.coroutine
    def _connect(self):
        try:
            self.websocket = yield websocket_connect(
                self.url, subprotocols=['auth_token', self.token])
        except HTTPClientError as exc:
            LOGGER.error("Websocket connection failed: %s", exc)
            return
        LOGGER.debug("Websocket connection opened.")

    @gen.coroutine
    def _listen_websocket(self):
        while True:
            try:
                data = yield self.websocket.read_message()
                if data is None:
                    LOGGER.debug("Websocket connection closed.")
                    tornado.ioloop.IOLoop.current().stop()
                    return
                # Print received data to stdout
                sys.stdout.write(data)
                sys.stdout.flush()
            except (WebSocketClosedError, StreamClosedError) as exc:
                LOGGER.error("Websocket connection failed: %s", exc)
                return

    def _listen_stdin(self):
        LOGGER.debug("Start listening to stdin")

        def _handle_stdin(file_descriptor, handler):
            # pylint:disable=unused-argument
            message = file_descriptor.readline().strip()
            self.websocket.write_message(message + '\n')
        ioloop = tornado.ioloop.IOLoop.current()
        ioloop.add_handler(sys.stdin, _handle_stdin,
                           tornado.ioloop.IOLoop.READ)

    @gen.coroutine
    def run(self):
        """Connect and listen to the websocket server and listen to stdin."""
        # Wait for connection
        yield self._connect()

        if self.websocket is None:
            tornado.ioloop.IOLoop.current().stop()
            return

        # Start stdin listener as background task
        self._listen_stdin()
        # Start websocket listener in a coroutine
        self._listen_websocket()
