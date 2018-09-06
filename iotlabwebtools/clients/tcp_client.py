"""Management of the TCP connection to a node."""

import socket
import logging

from tornado import gen, tcpclient
from tornado.iostream import StreamClosedError

LOGGER = logging.getLogger("iotlabwebtools")

NODE_TCP_PORT = 20000


class TCPClient(object):
    """Class that manages the TCP client connection to a node."""

    def __init__(self):
        self.ready = False
        self.node = None
        self._tcp = None
        self.on_close = None
        self.on_data = None

    def send(self, data):
        """Send data via the TCP connection."""
        if not self.ready:
            return
        self._tcp.write(data)

    def stop(self):
        """Stop the TCP connection and close any opened websocket."""
        if self.ready:
            self._tcp.close()
        else:
            self.on_close(self.node)

    @gen.coroutine
    def start(self, node, on_data, on_close):
        """Start the TCP connection and wait for incoming bytes."""
        self.ready = False
        self.node = node
        self.on_close = on_close
        self.on_data = on_data
        try:
            LOGGER.debug("Opening TCP connection to '%s:%d'",
                         node, NODE_TCP_PORT)
            self._tcp = yield tcpclient.TCPClient().connect(
                node, NODE_TCP_PORT)
            LOGGER.debug("TCP connection opened on '%s:%d'",
                         node, NODE_TCP_PORT)
        except (StreamClosedError, socket.gaierror):
            LOGGER.warning("Cannot open TCP connection to %s:%d",
                           node, NODE_TCP_PORT)
            # We can't connect to the node with TCP, closing all websockets
            self.stop()
            return
        self.ready = True
        self._read_stream()

    @gen.coroutine
    def _read_stream(self):
        LOGGER.debug("Listening to TCP connection for node %s:%d",
                     self.node, NODE_TCP_PORT)
        try:
            while True:
                data = yield self._tcp.read_bytes(1)
                try:
                    data_decoded = data.decode()
                except UnicodeDecodeError:
                    LOGGER.warning("Cannot decode data received via TCP.")
                    continue
                self.on_data(self.node, data_decoded)
        except StreamClosedError:
            self.ready = False
            self.stop()
            LOGGER.info("TCP connection to '%s' is closed.", self.node)
