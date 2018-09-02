
import json
import logging

from tornado import web

LOGGER = logging.getLogger("iotlabwebserial")


class HttpRequestHandler(web.RequestHandler):

    def _error(self, code, message):
        self.set_status(code)
        self.finish(message)

    def post(self):
        if not self.request.headers.get(
                "Content-Type", "").startswith("application/json"):
            return self._error(400, "Invalid content type")

        try:
            self.json_args = json.loads(self.request.body.decode())
        except ValueError:
            return self._error(400, "No json in request body")

        LOGGER.debug("Received json '%s'", self.json_args)
        if 'key' not in self.json_args:
            return self._error(400, "key is missing")
        if 'node' not in self.json_args:
            return self._error(400, "node is missing")

        node = self.json_args['node']
        key = self.json_args['key']
        LOGGER.debug("Received key '%s' for node '%s'", key, node)
        self.application.handle_http_post(node, key)
