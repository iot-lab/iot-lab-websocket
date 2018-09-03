"""iotlabwebserial HTTP request handler."""

import json
import logging

from tornado import web

LOGGER = logging.getLogger("iotlabwebserial")


class HttpRequestHandler(web.RequestHandler):
    # pylint:disable=abstract-method,arguments-differ
    """Class that handle HTTP POST requests."""

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
        if 'experiment_id' not in json_args:
            return self._error(400, "experiment_id is missing")
        experiment_id = json_args['experiment_id']

        if self.request.path.split('/')[-1] == "start":
            if 'nodes' not in json_args:
                return self._error(400, "nodes list is missing")
            nodes = json_args['nodes']

            if 'key' not in json_args:
                return self._error(400, "key is missing")
            key = json_args['key']

            LOGGER.debug("Start experiment '%s', with key '%s'",
                         experiment_id, key)
            self.application.handle_start_experiment(experiment_id, nodes, key)
        else:  # stop experiment
            LOGGER.debug("Stop experiment '%s'", experiment_id)
            self.application.handle_stop_experiment(experiment_id)
        return self.finish()
