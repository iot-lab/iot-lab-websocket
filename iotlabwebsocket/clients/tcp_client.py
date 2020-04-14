"""Management of the TCP connection to a node."""

import time
import socket

from tornado import gen, tcpclient
from tornado.iostream import StreamClosedError

from ..logger import LOGGER

NODE_TCP_PORT = 20000
CHUNK_SIZE = 1024
CHECK_BYTES_RECEIVED_PERIOD = 1  # seconds
MAX_BYTES_RECEIVED_PER_PERIOD = 15000


class TCPClient:
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

    @gen.coroutine
    def start(self, node, on_data, on_close):
        """Start the TCP connection and wait for incoming bytes."""
        self.ready = False
        self.node = node
        self.on_close = on_close
        self.on_data = on_data
        try:
            LOGGER.debug("Opening TCP connection to '%s:%d'", node, NODE_TCP_PORT)
            self._tcp = yield tcpclient.TCPClient().connect(node, NODE_TCP_PORT)
            LOGGER.debug("TCP connection opened on '%s:%d'", node, NODE_TCP_PORT)
        except (StreamClosedError, socket.gaierror):
            LOGGER.warning("Cannot open TCP connection to %s:%d", node, NODE_TCP_PORT)
            # We can't connect to the node with TCP, closing all websockets
            self.on_close(
                self.node, reason="Cannot connect to node {}".format(self.node)
            )
            return
        LOGGER.debug("TCP connection is ready")
        self.ready = True
        self._read_stream()

    @gen.coroutine
    def _read_stream(self):
        LOGGER.debug(
            "Listening to TCP connection for node %s:%d", self.node, NODE_TCP_PORT
        )
        received_bytes = 0
        start = time.time()
        try:
            while True:
                data = yield self._tcp.read_bytes(CHUNK_SIZE, partial=True)
                received_bytes += len(data)

                # Reset stream_byte every CHECK_BYTES_RECEIVED_PERIOD seconds
                if time.time() - start > CHECK_BYTES_RECEIVED_PERIOD:
                    if received_bytes > MAX_BYTES_RECEIVED_PER_PERIOD:
                        LOGGER.warning(
                            "Node %s is sending too fast, "
                            "received %d bytes in %d seconds, "
                            "closing.",
                            self.node,
                            received_bytes,
                            CHECK_BYTES_RECEIVED_PERIOD,
                        )
                        # Will close all websocket connections
                        # and as a consequence, close the TCP connection
                        self.on_close(
                            self.node,
                            reason=("Node {} is sending too fast".format(self.node)),
                        )
                    received_bytes = 0
                    start = time.time()

                self.on_data(self.node, data)
        except StreamClosedError:
            self.ready = False
            self.on_close(self.node, "Connection to {} is closed".format(self.node))
            LOGGER.info("TCP connection to '%s' is closed.", self.node)
