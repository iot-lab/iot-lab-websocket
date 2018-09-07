"""iotlabwebsocket http handler tests."""

import json
import logging
from collections import namedtuple

import tornado.testing

from iotlabwebsocket.web_application import WebApplication, DEFAULT_AUTH_URL

Response = namedtuple("Response", ["code", "body"])

LOGGER = logging.getLogger("iotlabwebsocket")
LOGGER.setLevel(logging.DEBUG)


class TestHttpAuthHandlerApp(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        return WebApplication(DEFAULT_AUTH_URL, 'token')

    def _check_request(self, expected_response, path='/experiments/123/token',
                       headers={"Content-Type": "application/json"}):
        response = self.fetch(path, method="GET", headers=headers)
        assert response.code == expected_response.code
        assert response.body == expected_response.body

    def test_valid_token_request(self):
        expected_response = Response(200,
                                     json.dumps({'token': 'token'}).encode())
        self._check_request(expected_response)

    def test_invalid_experiment_id(self):
        path = '/experiments//token'
        expected_response = Response(400, b'Invalid experiment id')
        self._check_request(expected_response, path=path)


class TestHttpAuthHandlerInvalidTokenApp(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        return WebApplication(DEFAULT_AUTH_URL)

    def test_invalid_token_request(self):
        expected_response = Response(400, b'No internal token set')
        response = self.fetch('/experiments/123/token', method="GET",
                              headers={"Content-Type": "application/json"})
        assert response.code == expected_response.code
        assert response.body == expected_response.body
