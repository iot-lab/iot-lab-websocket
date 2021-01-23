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
            LOGGER.debug(f"Opening TCP connection to '{node}:{NODE_TCP_PORT}'")
            self._tcp = yield tcpclient.TCPClient().connect(node, NODE_TCP_PORT)
            LOGGER.debug(f"TCP connection opened on '{node}:{NODE_TCP_PORT}'")
        except (StreamClosedError, socket.gaierror):
            LOGGER.warning(f"Cannot open TCP connection to {node}:{NODE_TCP_PORT}")
            # We can't connect to the node with TCP, closing all websockets
            self.on_close(self.node, reason=f"Cannot connect to node {self.node}")
            return
        LOGGER.debug("TCP connection is ready")
        self.ready = True
        self._read_stream()

    @gen.coroutine
    def _read_stream(self):
        LOGGER.debug(
            f"Listening to TCP connection for node {self.node}:{NODE_TCP_PORT}"
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
                            f"Node {self.node} is sending too fast, "
                            f"received {received_bytes} bytes in "
                            f"{CHECK_BYTES_RECEIVED_PERIOD} seconds, closing."
                        )
                        # Will close all websocket connections
                        # and as a consequence, close the TCP connection
                        self.on_close(
                            self.node,
                            reason=(f"Node {self.node} is sending too fast"),
                        )
                    received_bytes = 0
                    start = time.time()

                self.on_data(self.node, data)
        except StreamClosedError:
            self.ready = False
            self.on_close(self.node, f"Connection to {self.node} is closed")
            LOGGER.info(f"TCP connection to '{self.node} is closed.")
