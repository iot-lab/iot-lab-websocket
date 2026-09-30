"""iotlabwebserial HTTP request handler."""

import json

from tornado import web

from ..logger import LOGGER

NODES = {"nodes": ["localhost.local"]}


def _nodes():
    return json.dumps(NODES)


class HttpApiRequestHandler(web.RequestHandler):
    # pylint:disable=abstract-method,arguments-differ
    """Class that handle HTTP token requests."""

    token = None

    def initialize(self, token: str) -> None:
        """Initialize the authentication token during instantiation."""
        self.token = token

    def get(self) -> None:
        """Return the authentication token."""
        experiment_id = self.request.path.split("/")[-2]
        resource = self.request.path.split("/")[-1]

        if resource == "token":
            if not self.token:
                LOGGER.debug(
                    f"Token request for experiment id '{experiment_id}' failed."
                )
                self.set_status(400)
                self.finish("No internal token set")
                return
            LOGGER.debug(
                f"Received request token for experiment '{experiment_id}'"
            )
            LOGGER.debug(f"Internal token: '{self.token}'")
            self.set_header("Content-Type", "application/json")
            self.finish(json.dumps({"token": self.token}))
        elif not resource:
            self.set_header("Content-Type", "application/json")
            self.finish(_nodes())
        else:
            self.set_status(404)
            self.finish(f"Invalid resource '{resource}'")
