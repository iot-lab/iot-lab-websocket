"""iotlabwebserial HTTP request handler."""

import json
import logging

from tornado import web

LOGGER = logging.getLogger("iotlabwebtools")


class HttpAuthRequestHandler(web.RequestHandler):
    # pylint:disable=abstract-method,arguments-differ
    """Class that handle HTTP token requests."""

    def get(self):
        experiment_id = self.request.path.split('/')[-2]
        if not experiment_id:
            msg = "Invalid experiment id"
            LOGGER.debug("Token request for experiment id '%s' failed.",
                         experiment_id)
            self.set_status(400)
            self.finish(msg)
            return

        LOGGER.debug("Received request token for experiment '%s'",
                     experiment_id)
        self.request.headers["Content-Type"] = "application/json"
        self.write(json.dumps({"token": "token"}))
        self.finish()
