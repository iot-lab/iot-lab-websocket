"""iotlabwebserial http handler tests."""

import json
from collections import namedtuple

import tornado.testing

from iotlabwebserial.web_application import WebApplication

Response = namedtuple("Response", ["code", "body"])


class TestHttpHandlerApp(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        return WebApplication(debug=True)

    def _check_request(self, body, expected_response,
                       headers={"Content-Type": "application/json"}):
        response = self.fetch('/node/key', method="POST",
                              headers=headers,
                              body=body)
        assert response.code == expected_response.code
        assert response.body == expected_response.body

    def test_valid_post(self):
        data = json.dumps({"node": "localhost", "key": "key"})
        expected_response = Response(200, b'')
        self._check_request(data, expected_response)

    def test_invalid_url(self):
        response = self.fetch('/invalid', method="POST",
                              headers={"Content-Type": "application/json"})
        assert response.code != 200

    def test_invalid_contents(self):
        data = json.dumps({"node": "localhost", "key": "key"})
        expected_response = Response(400, b'Invalid content type')
        self._check_request(data, expected_response, headers="")

        expected_response = Response(400, b'No json in request body')
        self._check_request("No json", expected_response)

        invalid_data = json.dumps({"node": "localhost"})
        expected_response = Response(400, b'key is missing')
        self._check_request(invalid_data, expected_response)

        invalid_data = json.dumps({"key": "key"})
        expected_response = Response(400, b'node is missing')
        self._check_request(invalid_data, expected_response)
