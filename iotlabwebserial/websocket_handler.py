"""iotlabwebserial websocket connections handler."""

import logging

from tornado import websocket, gen

LOGGER = logging.getLogger("iotlabwebserial")


class WebsocketClientHandler(websocket.WebSocketHandler):
    # pylint:disable=abstract-method,arguments-differ
    """Class that manage websocket connections."""

    authentified = False

    def check_origin(self, origin):
        """Allow connections from anywhere."""
        return True

    def initialize(self, node):
        """Initialize the handler with the corresponding node hostname."""
        LOGGER.debug("Initialize webscocket handler for %s", node)
        self.node = node

    @gen.coroutine
    def open(self):
        """Accept all incoming connections.

        After 2s, if the connection is not authentified, it's closed.
        """
        self.set_nodelay(True)
        LOGGER.debug("Websocket connection opened for node '%s'", self.node)

        # Wait 3 seconds to get the gateway authentication token.
        yield gen.sleep(3)
        if not self.authentified:
            LOGGER.debug("No valid key received, closing websocket")
            self.close()

    @gen.coroutine
    def on_message(self, data):
        """Triggered when data is received from the websocket client."""
        if not self.authentified:
            # While not authentified, any message received should contain
            # an authentication key.
            expected_key = self.application.handlers[self.node].key
            LOGGER.debug("Websocket authentication, received key: %s, "
                         "expected key: %s", data, expected_key)
            self.authentified = (expected_key is not None and
                                 data == expected_key)
            if self.authentified:
                LOGGER.debug("Websocket authentication succeeded for node "
                             "'%s'", self.node)
                self.application.handle_websocket_validation(self)
        else:
            self.application.handle_websocket_data(self, data)

    def on_close(self):
        """Manage the disconnection of the websocket."""
        # Only authentified connections are handled by the main application.
        if self.authentified:
            self.application.handle_websocket_close(self)
        LOGGER.debug("Websocket connection closed for node '%s'", self.node)
