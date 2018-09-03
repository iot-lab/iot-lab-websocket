"""Management of the TCP connection to a node."""

import logging

from tornado import gen, tcpclient
from tornado.iostream import StreamClosedError

LOGGER = logging.getLogger("iotlabwebserial")


class NodeHandler(object):
    """Class that manages the TCP connection to a node."""

    def __init__(self, debug=False):
        self.websockets = list()
        self.tcp_ready = False
        self.node = None
        self.key = None
        self._tcp = None

        if debug:
            LOGGER.setLevel(logging.DEBUG)

    def send(self, data):
        """Send data via the TCP connection."""
        if not self.tcp_ready:
            return
        self._tcp.write(data)

    def stop(self):
        """Stop the TCP connection and close any opened websocket."""
        if self.tcp_ready:
            self._tcp.close()
        for websocket in self.websockets:
            websocket.close()

    @gen.coroutine
    def start(self, node, port):
        """Start the TCP connection and wait for incoming bytes."""
        self.tcp_ready = False
        self.node = node
        try:
            LOGGER.debug("Opening TCP connection to '%s:%d'", node, port)
            self._tcp = yield tcpclient.TCPClient().connect(node, port)
            LOGGER.debug("TCP connection opened on '%s:%d'", node, port)
        except StreamClosedError:
            LOGGER.debug("Cannot open TCP connection to %s:%s", node, port)
            # We can't connect to the node with TCP, closing all websockets
            self.stop()
            return
        self.tcp_ready = True
        self._read_stream()

    @gen.coroutine
    def _read_stream(self):
        LOGGER.debug("Listening to TCP connection.")
        try:
            while True:
                data = yield self._tcp.read_bytes(1)
                try:
                    data_decoded = data.decode()
                except UnicodeDecodeError:
                    LOGGER.debug("Cannot decode data received via TCP.")
                    continue
                for websocket in self.websockets:
                    if websocket.authentified:
                        websocket.write_message(data_decoded)
        except StreamClosedError:
            self.tcp_ready = False
            self.stop()
            LOGGER.debug("TCP connection to '%s' is closed.", self.node)
