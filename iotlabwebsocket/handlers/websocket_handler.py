"""iotlabwebserial websocket connections handler."""

import asyncio
import hmac

from tornado import websocket
from tornado.httpclient import HTTPClientError

from ..api import ApiClient
from ..logger import LOGGER

# Node output waiting to be sent to a websocket client, in bytes. Above
# this, the client is considered stalled and is disconnected: Tornado keeps
# everything not yet sent in memory, so a client that stops reading would
# otherwise make the service memory grow without limit. A node sends at most
# 15 kB per second, so this is about a minute of its output.
MAX_PENDING_BYTES = 1_000_000


class WebsocketClientHandler(websocket.WebSocketHandler):
    # pylint:disable=abstract-method,arguments-differ
    # pylint:disable=attribute-defined-outside-init,too-many-instance-attributes
    """Class that manage websocket connections."""

    def _check_path(self) -> None:
        # Path structure is guaranteed correct by the routing regex.
        path_elems = self.request.path.split("/")
        if self.text:
            self.site, self.experiment_id, self.node = path_elems[-4:-1]
        else:
            self.site, self.experiment_id, self.node = path_elems[-5:-2]

    def select_subprotocol(self, subprotocols: list[str]) -> str | None:
        """Only accept the 'token' subprotocol"""
        if "token" in subprotocols:
            return "token"
        return None

    def _check_subprotocols(self, subprotocols: list[str]) -> bool:
        if len(subprotocols) != 3 or subprotocols[1].strip() != "token":
            LOGGER.warning("Reject websocket connection: invalid subprotocol")
            self.set_status(401)  # Authentication failed
            self.finish("Invalid subprotocols")
            return False
        return True

    async def _fetch_experiment(self) -> tuple[str, list[str]]:
        # Both requests are sent together: the connection waits for one API
        # round trip instead of two.
        results = await asyncio.gather(
            self.api.fetch_token_async(self.experiment_id),
            self.api.fetch_nodes_async(self.experiment_id),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                raise result
        api_token, nodes = results
        return api_token, nodes

    def _check_token(self, req_token: str, api_token: str) -> bool:
        # Token values are never logged or echoed: they give access to the
        # nodes of the experiment.
        LOGGER.debug(f"Fetched token for experiment id '{self.experiment_id}'")

        # Constant time comparison: the answer time does not tell how much
        # of a guessed token is right.
        if not hmac.compare_digest(req_token.encode(), api_token.encode()):
            LOGGER.warning(
                "Reject websocket connection: invalid token for experiment "
                f"id '{self.experiment_id}'"
            )
            self.set_status(401)  # Authentication failed
            self.finish("Invalid token")
            return False

        LOGGER.debug("Provided token verified")
        return True

    def _check_node(self, nodes: list[str]) -> bool:
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

    def _reject_api_error(self, exc: Exception) -> None:
        # The API refuses the request (unknown experiment, no access): the
        # connection is not authorized. Otherwise it cannot be checked.
        if isinstance(exc, HTTPClientError) and 400 <= exc.code < 500:
            LOGGER.warning(
                f"Reject websocket connection: experiment "
                f"'{self.experiment_id}' refused by the API ({exc})"
            )
            self.set_status(401)  # Authentication failed
            self.finish("Invalid experiment")
            return
        LOGGER.error(
            f"Cannot check websocket connection with the API: {exc!r}"
        )
        self.set_status(503)
        self.finish("Authentication service unavailable")

    def initialize(self, api: ApiClient, text: bool) -> None:
        """Initialize the api and binary information."""
        self.api = api
        self.text = text
        self.pending_bytes = 0
        self.stalled = False

    def write_node_data(
        self, message: str | bytes, size: int, binary: bool = False
    ) -> None:
        """Send node output, disconnecting a client that does not read it.

        size is the number of bytes of node output carried by message.
        """
        if self.stalled:
            return
        if self.pending_bytes + size > MAX_PENDING_BYTES:
            self.stalled = True
            LOGGER.warning(
                f"Close websocket for node '{self.node}': client does not "
                f"read the node output, {self.pending_bytes} bytes pending"
            )
            self.close(
                code=1008, reason="Client does not read the node output"
            )
            return
        future = self.write_message(message, binary=binary)
        self.pending_bytes += size
        future.add_done_callback(
            lambda written: self._on_written(written, size)
        )

    def _on_written(self, future: asyncio.Future, size: int) -> None:
        self.pending_bytes -= size
        # A write failing because the connection closed is handled by
        # on_close: only mark the error as retrieved.
        if not future.cancelled():
            future.exception()

    async def get(self, *args, **kwargs):  # pylint: disable=invalid-overridden-method
        """Triggered before any websocket connection is opened.

        The url path, validated by the routing regex, is in the form
        /ws/<site>/<experiment_id>/<node>/serial, with a /raw suffix for
        binary streams.
        This method checks that the token provided in the websocket
        connection matches the corresponding one generated on the
        authentication host.
        Finally, it checks that the requested node belongs to the experiment
        and the site.
        """

        LOGGER.info("Websocket connection request")

        # Check path is always True
        self._check_path()

        subprotocols = self.request.headers.get(
            "Sec-WebSocket-Protocol", ""
        ).split(",")
        if not self._check_subprotocols(subprotocols):
            return

        self.user = subprotocols[0].strip()

        try:
            api_token, nodes = await self._fetch_experiment()
        except (HTTPClientError, OSError, ValueError, KeyError) as exc:
            # API refusal or unreachable API, invalid JSON or missing field
            self._reject_api_error(exc)
            return

        # Verify the token provided in subprotocols
        if not self._check_token(subprotocols[2].strip(), api_token):
            return

        # Check that the requested node is in the experiment
        if not self._check_node(nodes):
            return

        # Let parent class correctly configure the websocket connection
        await super().get(*args, **kwargs)

        LOGGER.info(
            f"Websocket connection for experiment '{self.experiment_id}' "
            f"on node '{self.node}'"
        )

    def check_origin(self, origin: str) -> bool:
        """Allow connections from anywhere."""
        return True

    def open(self) -> None:
        """Accept all incoming connections."""
        self.set_nodelay(True)
        LOGGER.debug(f"Websocket connection opened for node '{self.node}'")
        self.application.handle_websocket_open(self)

    def on_message(self, message: str | bytes) -> None:
        """Triggered when data is received from the websocket client."""
        if self.text:
            try:
                data = message.encode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
                return
        else:
            data = message
        self.application.handle_websocket_data(self, data)

    def on_close(self) -> None:
        """Manage the disconnection of the websocket."""
        LOGGER.info(
            f"Websocket connection closed for node '{self.node}', "
            f"code: {self.close_code}, reason: '{self.close_reason}'"
        )
        self.application.handle_websocket_close(self)
