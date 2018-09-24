"""iotlabwebserial HTTP request handler."""

import json

from tornado import web

from ..logger import LOGGER

NODES = {'nodes': ['localhost.local']}


def _nodes():
    return json.dumps(NODES)


class HttpApiRequestHandler(web.RequestHandler):
    # pylint:disable=abstract-method,arguments-differ
    """Class that handle HTTP token requests."""

    def initialize(self, token):
        """Initialize the authentication token during instantiation."""
        self.token = token

    def get(self):
        """Return the authentication token."""

        experiment_id = self.request.path.split('/')[-2]
        resource = self.request.path.split('/')[-1]

        self.request.headers["Content-Type"] = "application/json"
        if resource == 'token':
            msg = None
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
            self.write(json.dumps({"token": self.token}))
        elif not resource:
            self.write(_nodes())
        else:
            self.set_status(404)
            self.finish("Invalid resource '{}'".format(resource))
            return
        self.finish()
