"""iotlabwebserial HTTP request handler."""

import json
import logging

from tornado import web

LOGGER = logging.getLogger("iotlabwebserial")


class HttpRequestHandler(web.RequestHandler):
    # pylint:disable=abstract-method,arguments-differ
    """Class that handle HTTP requests."""

    def _error(self, code, message):
        self.set_status(code)
        return self.finish(message)

    def post(self):
        if not self.request.headers.get(
                "Content-Type", "").startswith("application/json"):
            return self._error(400, "Invalid content type")

        try:
            json_args = json.loads(self.request.body.decode())
        except ValueError:
            return self._error(400, "No json in request body")

        LOGGER.debug("Received json '%s'", json_args)
        if 'key' not in json_args:
            return self._error(400, "key is missing")
        if 'node' not in json_args:
            return self._error(400, "node is missing")

        node = json_args['node']
        key = json_args['key']
        LOGGER.debug("Received key '%s' for node '%s'", key, node)
        self.application.handle_http_post(node, key)
        return self.finish()
