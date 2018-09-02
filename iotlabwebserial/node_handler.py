"""Management of the TCP connection to a node."""

import logging

from tornado import gen, tcpclient
from tornado.iostream import StreamClosedError

LOGGER = logging.getLogger(__file__)


class NodeHandler(object):

    def __init__(self, debug=False):
        self.websockets = list()
        self.tcp_ready = False
        self.node = None

        if debug:
            LOGGER.setLevel(logging.DEBUG)

    def _close_all_websockets(self):
        for ws in self.websockets:
            ws.close()

    @gen.coroutine
    def start_tcp_connection(self, node, port):
        self.tcp_ready = False
        self.node = node
        try:
            LOGGER.debug("Opening TCP connection to '%s:%d'", node, port)
            self.tcp = yield tcpclient.TCPClient().connect(
                node, port)
            LOGGER.debug("TCP connection opened on '%s:%d'", node, port)
        except StreamClosedError:
            LOGGER.debug("Cannot open TCP connection to %s:%s", node, port)
            # We can't connect to the node with TCP, closing all websockets
            self._close_all_websockets()
            return
        self.tcp_ready = True
        self._read_stream()

    @gen.coroutine
    def _read_stream(self):
        LOGGER.debug("Listening to TCP connection.")
        try:
            while True:
                data = yield self.tcp.read_bytes(1)
                try:
                    data_decoded = data.decode()
                except UnicodeDecodeError:
                    LOGGER.debug("Cannot decode data received via TCP.")
                    continue
                for ws in self.websockets:
                    if ws.authentified:
                        ws.write_message(data_decoded)
        except StreamClosedError:
            self.tcp_ready = False
            self._close_all_websockets()
            LOGGER.debug("TCP connection to '%s' is closed.", self.node)
