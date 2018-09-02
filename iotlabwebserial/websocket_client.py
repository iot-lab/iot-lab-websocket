"""Websocket client"""

import sys
import logging

import tornado
from tornado import gen
from tornado.websocket import websocket_connect, WebSocketClosedError

LOGGER = logging.getLogger("websocketclient")


class WebsocketClient(object):
    # pylint:disable=too-few-public-methods
    """Class that connects to a websocket server while listening to stdin."""

    def __init__(self, url, key, debug=False):
        if debug:
            LOGGER.setLevel(logging.DEBUG)
        self.url = url
        self.key = key
        self.websocket = None

    @gen.coroutine
    def _connect(self):
        try:
            self.websocket = yield websocket_connect(self.url)
        except WebSocketClosedError:
            LOGGER.error("Websocket connection failed.")
            return

        LOGGER.debug("Websocket connection opened.")
        # Send the authentication key once connected
        self.websocket.write_message(self.key)

    @gen.coroutine
    def _listen_websocket(self):
        while True:
            data = yield self.websocket.read_message()
            if data is None:
                LOGGER.debug("Websocket connection closed.")
                tornado.ioloop.IOLoop.current().stop()
                return
            # Print received data to stdout
            sys.stdout.write(data)
            sys.stdout.flush()

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
