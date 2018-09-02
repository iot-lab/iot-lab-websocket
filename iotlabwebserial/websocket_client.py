"""Websocket client"""

import sys
import argparse
import logging

import tornado
from tornado import gen
from tornado.websocket import websocket_connect

LOGGER = logging.getLogger("websocketclient")


class WebsocketClient(object):

    def __init__(self, url, key, debug=False):
        if debug:
            LOGGER.setLevel(logging.DEBUG)
        self.url = url
        self.key = key
        self.ws = None

    @gen.coroutine
    def _connect(self):
        try:
            self.ws = yield websocket_connect(self.url)
        except Exception:
            LOGGER.error("Websocket connection failed.")
            return

        LOGGER.debug("Websocket connection opened.")
        # Send the authentication key once connected
        self.ws.write_message(self.key)

    @gen.coroutine
    def run(self):
        # Wait for connection
        yield self._connect()

        if self.ws is None:
            tornado.ioloop.IOLoop.current().stop()
            return

        # Start stdin listener as background task
        self._listen_stdin()
        # Start websocket listener in a coroutine
        self._listen_websocket()

    @gen.coroutine
    def _listen_websocket(self):
        while True:
            data = yield self.ws.read_message()
            if data is None:
                LOGGER.debug("Websocket connection closed.")
                tornado.ioloop.IOLoop.current().stop()
                return
            # Print received data to stdout
            sys.stdout.write(data)
            sys.stdout.flush()

    def _listen_stdin(self):
        LOGGER.debug("Start listening to stdin")

        def handle_stdin(fd, handler):
            message = fd.readline().strip()
            self.ws.write_message(message + '\n')
        ioloop = tornado.ioloop.IOLoop.current()
        ioloop.add_handler(sys.stdin, handle_stdin, tornado.ioloop.IOLoop.READ)
