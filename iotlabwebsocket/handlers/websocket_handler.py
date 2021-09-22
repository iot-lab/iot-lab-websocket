"""iotlabwebserial websocket connections handler."""

from tornado import websocket, gen

from ..logger import LOGGER


class WebsocketClientHandler(websocket.WebSocketHandler):
    # pylint:disable=abstract-method,arguments-differ
    # pylint:disable=attribute-defined-outside-init
    """Class that manage websocket connections."""

    def _check_path(self):
        # Check path is always correct
        path_elems = self.request.path.split("/")
        if self.text:
            self.site, self.experiment_id, self.node = path_elems[-4:-1]
        else:
            self.site, self.experiment_id, self.node = path_elems[-5:-2]
        return True

    def select_subprotocol(self, subprotocols):
        """Only accept the 'token' subprotocol"""
        if "token" in subprotocols:
            return "token"
        return None

    @gen.coroutine
    def _check_subprotocols(self, subprotocols):
        if len(subprotocols) != 3 or subprotocols[1].strip() != "token":
            LOGGER.warning("Reject websocket connection: invalib subprotocol")
            self.set_status(401)  # Authentication failed
            self.finish("Invalid subprotocols")
            return False

        req_token = subprotocols[2].strip()

        # Fetch the token from the authentication server
        api_token = yield self.api.fetch_token_async(self.experiment_id)

        LOGGER.debug(
            "Fetched token '%s' for experiment id '%s'", api_token, self.experiment_id
        )

        if req_token != api_token:
            LOGGER.warning(f"Reject websocket connection: invalib token '{req_token}'")
            self.set_status(401)  # Authentication failed
            self.finish(f"Invalid token '{req_token}'")
            return False

        LOGGER.debug(f"Provided token '{req_token}' verified")
        return True

    @gen.coroutine
    def _check_node(self):
        nodes = yield self.api.fetch_nodes_async(self.experiment_id)
        for node in nodes:
            node_elem = node.split(".")
            if node_elem[0] == self.node and node_elem[1] == self.site:
                LOGGER.debug("Requested node found in experiment")
                return True

        LOGGER.warning(
            f"Invalid node '{self.node}' for experiment id "
            f"'{self.experiment_id}' in site '{self.site}'"
        )
        # No node matches the requested ressource for the experiment and site.
        self.set_status(401)  # Authentication failed
        self.finish("Invalid node")
        return False

    def initialize(self, api, text):
        """Initialize the api and binary information."""
        self.api = api
        self.text = text

    @gen.coroutine
    def get(self, *args, **kwargs):  # pylint: disable=invalid-overridden-method
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
        subprotocols = self.request.headers.get("Sec-WebSocket-Protocol", "").split(",")
        valid_subprotocols = yield self._check_subprotocols(subprotocols)
        if not valid_subprotocols:
            return

        self.user = subprotocols[0].strip()

        # Check that the requested node is in the experiment
        node_valid = yield self._check_node()
        if not node_valid:
            return

        # Let parent class correctly configure the websocket connection
        yield super(WebsocketClientHandler, self).get(*args, **kwargs)

        LOGGER.info(
            f"Websocket connection for experiment '{self.experiment_id}' "
            f"on node '{self.node}'"
        )

    def check_origin(self, origin):
        """Allow connections from anywhere."""
        return True

    @gen.coroutine
    def open(self):
        """Accept all incoming connections.

        After 2s, if the connection is not authentified, it's closed.
        """
        self.set_nodelay(True)
        LOGGER.debug(f"Websocket connection opened for node '{self.node}'")
        self.application.handle_websocket_open(self)

    @gen.coroutine
    def on_message(self, message):
        """Triggered when data is received from the websocket client."""
        if self.text:
            try:
                data = message.encode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
                return
        else:
            data = message
        self.application.handle_websocket_data(self, data)

    def on_close(self):
        """Manage the disconnection of the websocket."""
        LOGGER.info(
            f"Websocket connection closed for node '{self.node}', "
            f"code: {self.close_code}, reason: '{self.close_reason}'"
        )
        self.application.handle_websocket_close(self)
