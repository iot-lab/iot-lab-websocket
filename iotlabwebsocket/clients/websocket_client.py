"""Websocket client"""

import sys

import tornado
from tornado import gen
from tornado.websocket import websocket_connect
from tornado.httpclient import HTTPClientError

from ..logger import CLIENT_LOGGER as LOGGER


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
                self.url, subprotocols=['token', self.token])
        except HTTPClientError as exc:
            LOGGER.error("Websocket connection failed: %s", exc)
            return
        LOGGER.debug("Websocket connection opened.")

    @gen.coroutine
    def _listen_websocket(self):
        while True:
            data = yield self.websocket.read_message()
            if data is None:
                LOGGER.debug("Websocket connection closed.")
                # Let some time to the loop to catch any pending exception
                yield gen.sleep(0.1)
                tornado.ioloop.IOLoop.instance().stop()
                return
            # Print received data to stdout
            sys.stdout.write(data)
            sys.stdout.flush()

    @gen.coroutine
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
            raise gen.Return()

        # Start stdin listener as background task
        yield self._listen_stdin()
        # Start websocket listener
        yield self._listen_websocket()
