"""iotlabwebserial http handler tests."""

import json
import logging
from collections import namedtuple

import tornado.testing

from iotlabwebserial.web_application import WebApplication

Response = namedtuple("Response", ["code", "body"])

LOGGER = logging.getLogger("iotlabwebserial")
LOGGER.setLevel(logging.DEBUG)


class TestHttpHandlerApp(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        return WebApplication(['localhost'])

    def _check_request(self, body, expected_response,
                       headers={"Content-Type": "application/json"},
                       path='/experiment/start'):
        response = self.fetch(path, method="POST", headers=headers, body=body)
        assert response.code == expected_response.code
        assert response.body == expected_response.body

    def test_valid_start_post(self):
        data = json.dumps({"experiment_id": 1234, "key": "key",
                          "nodes": ['node1', 'node2']})
        expected_response = Response(200, b'')
        self._check_request(data, expected_response)

    def test_valid_stop_post(self):
        data = json.dumps({"experiment_id": 1234})
        expected_response = Response(200, b'')
        self._check_request(data, expected_response, path='/experiment/stop')

    def test_invalid_url(self):
        response = self.fetch('/invalid', method="POST",
                              headers={"Content-Type": "application/json"})
        assert response.code != 200

    def test_invalid_start_contents(self):
        data = json.dumps({"experiment_id": 1234, "key": "key"})
        expected_response = Response(400, b'Invalid content type')
        self._check_request(data, expected_response, headers="")

        expected_response = Response(400, b'No json in request body')
        self._check_request("No json", expected_response)

        invalid_data = json.dumps({"experiment_id": 1234})
        expected_response = Response(400, b'nodes list is missing')
        self._check_request(invalid_data, expected_response)

        invalid_data = json.dumps({"experiment_id": 1234, "nodes": ['1', '2']})
        expected_response = Response(400, b'key is missing')
        self._check_request(invalid_data, expected_response)

        invalid_data = json.dumps({"key": "key"})
        expected_response = Response(400, b'experiment_id is missing')
        self._check_request(invalid_data, expected_response)

        invalid_data = json.dumps({"nodes": ['1', '2']})
        expected_response = Response(400, b'experiment_id is missing')
        self._check_request(invalid_data, expected_response)

    def test_invalid_stop_contents(self):
        stop_path = '/experiment/stop'
        invalid_data = json.dumps({"experiment": 1234})
        expected_response = Response(400, b'experiment_id is missing')
        self._check_request(invalid_data, expected_response, path=stop_path)
