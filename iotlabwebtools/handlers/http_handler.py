"""iotlabwebserial HTTP request handler."""

import json
import logging

from tornado import web

LOGGER = logging.getLogger("iotlabwebtools")


class HttpAuthRequestHandler(web.RequestHandler):
    # pylint:disable=abstract-method,arguments-differ
    """Class that handle HTTP token requests."""

    def initialize(self, token):
        """Initialize the authentication token during instantiation."""
        self.token = token

    def get(self):
        """Return the authentication token."""
        experiment_id = self.request.path.split('/')[-2]

        msg = None
        if not experiment_id:
            msg = "Invalid experiment id"

        if not self.token:
            msg = "No internal token set"

        if msg is not None:
            LOGGER.debug("Token request for experiment id '%s' failed.",
                         experiment_id)
            self.set_status(400)
            self.finish(msg)
            return

        LOGGER.debug("Received request token for experiment '%s'",
                     experiment_id)
        LOGGER.debug("Internal token: '%s'", self.token)
        self.request.headers["Content-Type"] = "application/json"
        self.write(json.dumps({"token": self.token}))
        self.finish()
