"""iotlabwebserial websocket connections handler."""

import json
import logging

from tornado import websocket, gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

LOGGER = logging.getLogger("iotlabwebtools")


class WebsocketClientHandler(websocket.WebSocketHandler):
    # pylint:disable=abstract-method,arguments-differ
    """Class that manage websocket connections."""

    def _check_path(self):
        # Check path is correct
        path = self.request.path
        path_elements = path.split('/')
        msg = None
        if len(path_elements) != 4:
            msg = "invalid url {}".format(path)

        experiment_id, node = path_elements[-2:]
        if not experiment_id or not node:
            msg = "invalid url: {}".format(path)

        if msg is not None:
            LOGGER.warning("Reject websocket connection: %s", msg)
            self.set_status(404)  # Not found
            self.finish(msg)
            return False

        self.experiment_id, self.node = path_elements[-2:]
        return True

    @gen.coroutine
    def _check_token(self):
        subprotocols = self.request.headers.get(
            "Sec-WebSocket-Protocol", "").split(',')
        if len(subprotocols) != 2 or subprotocols[0] != 'auth_token':
            LOGGER.warning("Reject websocket connection: invalib subprotocol")
            self.set_status(401)  # Authentication failed
            self.finish("Invalid subprotocols")
            return False

        token = subprotocols[1]

        # Fetch the token from the authentication server
        http_client = AsyncHTTPClient()
        request = HTTPRequest("{}/{}/token".format(self.auth_url,
                                                   self.experiment_id))
        try:
            response = yield http_client.fetch(request)
        except Exception as exc:
            LOGGER.warning("Failed to fetch token: %s", exc)
            self.set_status(401)  # Authentication failed
            self.finish("Failed to fetch token")
            return False

        try:
            auth_token = json.loads(response.body.decode())['token']
        except json.JSONDecodeError as exc:
            LOGGER.warning("Cannot decode token: %s", exc)

        LOGGER.debug("Fetched token '%s' for experiment id '%s'",
                     auth_token, self.experiment_id)

        if token != auth_token:
            LOGGER.warning("Reject websocket connection: invalib token")
            self.set_status(401)  # Authentication failed
            self.finish("Invalid token")
            return False

        return True

    def initialize(self, auth_url=""):
        """Initialize the authentication url where tokens are retrieved."""
        self.auth_url = auth_url

    @gen.coroutine
    def get(self, *args, **kwargs):
        """Triggered before any websocket connection is opened.

        This method checks if the url path is valid: the url path be in the
        form /ws/<experiment_id>/<node_id>.
        This method also checks that the token provided in the websocket
        connection matches the corresponding one generated on the
        authentication host.
        """
        # Check path is correct
        if not self._check_path():
            return

        # Verify token provided in subprotocols, since there's an asynchronous
        # call to the API, we wait for it to complete.
        token_valid = yield self._check_token()
        if not token_valid:
            return

        LOGGER.info("Websocket connection for experiment '%s' on node '%s'",
                    self.experiment_id, self.node)

        # Let parent class correctly configure the websocket connection
        super(WebsocketClientHandler, self).get(*args, **kwargs)

    def check_origin(self, origin):
        """Allow connections from anywhere."""
        return True

    @gen.coroutine
    def open(self):
        """Accept all incoming connections.

        After 2s, if the connection is not authentified, it's closed.
        """
        self.set_nodelay(True)
        LOGGER.debug("Websocket connection opened for node '%s'", self.node)
        self.application.handle_websocket_open(self)

    @gen.coroutine
    def on_message(self, data):
        """Triggered when data is received from the websocket client."""
        self.application.handle_websocket_data(self, data)

    def on_close(self):
        """Manage the disconnection of the websocket."""
        LOGGER.info("Websocket connection closed for node '%s'", self.node)
        self.application.handle_websocket_close(self)
