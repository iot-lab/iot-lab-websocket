"""iotlabwebserial websocket connections handler."""

from tornado import websocket, gen

from ..logger import LOGGER


class WebsocketClientHandler(websocket.WebSocketHandler):
    # pylint:disable=abstract-method,arguments-differ
    # pylint:disable=attribute-defined-outside-init
    """Class that manage websocket connections."""

    def _check_path(self):
        # Check path is always correct
        path = self.request.path
        self.site, self.experiment_id, self.node = path.split('/')[-4:-1]
        return True

    def select_subprotocol(self, subprotocols):
        """Only accept the 'token' subprotocol"""
        if "token" in subprotocols:
            return "token"
        return None

    @gen.coroutine
    def _check_token(self):
        subprotocols = self.request.headers.get(
            "Sec-WebSocket-Protocol", "").split(',')
        if len(subprotocols) != 2 or subprotocols[0].strip() != 'token':
            LOGGER.warning("Reject websocket connection: invalib subprotocol")
            self.set_status(401)  # Authentication failed
            self.finish("Invalid subprotocols")
            raise gen.Return(False)

        req_token = subprotocols[1].strip()

        # Fetch the token from the authentication server
        api_token = yield self.api.fetch_token_async(self.experiment_id)

        LOGGER.debug("Fetched token '%s' for experiment id '%s'",
                     api_token, self.experiment_id)

        if req_token != api_token:
            LOGGER.warning("Reject websocket connection: invalib token '%s'",
                           req_token)
            self.set_status(401)  # Authentication failed
            self.finish("Invalid token '{}'".format(req_token))
            raise gen.Return(False)

        LOGGER.debug("Provided token '%s' verified", req_token)
        raise gen.Return(True)

    @gen.coroutine
    def _check_node(self):
        nodes = yield self.api.fetch_nodes_async(self.experiment_id)
        for node in nodes:
            node_elem = node.split('.')
            if node_elem[0] == self.node and node_elem[1] == self.site:
                LOGGER.debug("Requested node found in experiment")
                raise gen.Return(True)

        LOGGER.warning("Invalid node '%s' for experiment id '%s' in site "
                       "'%s'", self.node, self.experiment_id, self.site)
        # No node matches the requested ressource for the experiment and site.
        self.set_status(401)  # Authentication failed
        self.finish("Invalid node")
        raise gen.Return(False)

    def initialize(self, api):
        """Initialize the api information."""
        self.api = api

    @gen.coroutine
    def get(self, *args, **kwargs):
        """Triggered before any websocket connection is opened.

        This method checks if the url path is valid: the url path be in the
        form /ws/<experiment_id>/<node_id>.
        This method also checks that the token provided in the websocket
        connection matches the corresponding one generated on the
        authentication host.
        Finally, it checks that the requested node belongs to the experiment
        and the site.
        """

        LOGGER.info("Websocket connection request")

        # Check path is always True
        self._check_path()

        # Verify token provided in subprotocols, since there's an asynchronous
        # call to the API, we wait for it to complete.
        token_valid = yield self._check_token()
        if not token_valid:
            return

        # Check that the requested node is in the experiment
        node_valid = yield self._check_node()
        if not node_valid:
            return

        # Let parent class correctly configure the websocket connection
        super(WebsocketClientHandler, self).get(*args, **kwargs)

        LOGGER.info("Websocket connection for experiment '%s' on node '%s'",
                    self.experiment_id, self.node)

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
        LOGGER.info("Websocket connection closed for node '%s', code: %d, "
                    "reason: '%s'",
                    self.node, self.close_code, self.close_reason)
        self.application.handle_websocket_close(self)
