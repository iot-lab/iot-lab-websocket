"""Management of the TCP connection to a node."""

import asyncio
import socket
import time
from collections.abc import Callable

from tornado import tcpclient
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

    def send(self, data: bytes) -> None:
        """Send data via the TCP connection."""
        if not self.ready:
            return
        self._tcp.write(data)

    def stop(self) -> None:
        """Stop the TCP connection and close any opened websocket."""
        if self.ready:
            self._tcp.close()

    async def start(
        self,
        node: str,
        on_data: Callable[[str, bytes], None],
        on_close: Callable[..., None],
    ) -> None:
        """Start the TCP connection and wait for incoming bytes."""
        self.ready = False
        self.node = node
        self.on_close = on_close
        self.on_data = on_data
        try:
            LOGGER.debug(f"Opening TCP connection to '{node}:{NODE_TCP_PORT}'")
            self._tcp = await tcpclient.TCPClient().connect(
                node, NODE_TCP_PORT
            )
            LOGGER.debug(f"TCP connection opened on '{node}:{NODE_TCP_PORT}'")
        except (StreamClosedError, socket.gaierror):
            LOGGER.warning(
                f"Cannot open TCP connection to {node}:{NODE_TCP_PORT}"
            )
            self.on_close(
                self.node, reason=f"Cannot connect to node {self.node}"
            )
            return
        LOGGER.debug("TCP connection is ready")
        self.ready = True
        asyncio.ensure_future(self._read_stream())

    async def _read_stream(self) -> None:
        LOGGER.debug(
            f"Listening to TCP connection for node {self.node}:{NODE_TCP_PORT}"
        )
        received_bytes = 0
        start = time.time()
        try:
            while True:
                data = await self._tcp.read_bytes(CHUNK_SIZE, partial=True)
                received_bytes += len(data)

                # Reset stream_byte every CHECK_BYTES_RECEIVED_PERIOD seconds
                if time.time() - start > CHECK_BYTES_RECEIVED_PERIOD:
                    if received_bytes > MAX_BYTES_RECEIVED_PER_PERIOD:
                        LOGGER.warning(
                            f"Node {self.node} is sending too fast, "
                            f"received {received_bytes} bytes in "
                            f"{CHECK_BYTES_RECEIVED_PERIOD} seconds, closing."
                        )
                        self.on_close(
                            self.node,
                            reason=(f"Node {self.node} is sending too fast"),
                        )
                        return
                    received_bytes = 0
                    start = time.time()

                self.on_data(self.node, data)
        except StreamClosedError:
            self.ready = False
            self.on_close(self.node, f"Connection to {self.node} is closed")
            LOGGER.info(f"TCP connection to '{self.node} is closed.")
