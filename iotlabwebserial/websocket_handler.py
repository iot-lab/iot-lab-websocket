
import logging

from tornado import websocket, gen

LOGGER = logging.getLogger("iotlabwebserial")


class WebsocketClientHandler(websocket.WebSocketHandler):
    
    authentified = False

    def check_origin(self, origin):
        """Allow connections from anywhere."""
        return True

    def initialize(self, node):
        LOGGER.debug("Initialize webscocket handler for %s", node)
        self.node = node

    @gen.coroutine
    def open(self):
        """Discover nodes on each opened connection."""
        self.set_nodelay(True)
        LOGGER.debug("Websocket connection opened for node '%s'", self.node)

        # Wait 3 seconds to get the gateway authentication token.
        yield gen.sleep(2)
        if not self.authentified:
            LOGGER.debug("No valid key received, closing websocket")
            self.close()

    @gen.coroutine
    def on_message(self, message):
        """Triggered when a message is received from the web client."""
        if not self.authentified:
            expected_key = self.application.handlers[self.node].key
            LOGGER.debug("Websocket authentication, received key: %s, "
                         "expected key: %s", message, expected_key)
            self.authentified = (expected_key is not None and 
                                 message == expected_key)
            if self.authentified:
                LOGGER.debug("Websocket authentication succeeded for node "
                             "'%s'", self.node)
                self.application.handle_websocket_validation(self)
        else:
            self.application.handle_websocket_message(self, message)

    def on_close(self):
        """Remove websocket from internal list."""
        if self.authentified:
            self.application.handle_websocket_close(self)
        LOGGER.debug("Websocket connection closed for node '%s'", self.node)
