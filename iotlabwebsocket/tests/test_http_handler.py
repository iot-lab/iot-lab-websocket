"""iotlabwebsocket http handler tests."""

import json
from collections import namedtuple

import tornado.testing

from iotlabwebsocket.api import ApiClient
from iotlabwebsocket.handlers.http_handler import NODES
from iotlabwebsocket.web_application import WebApplication

Response = namedtuple("Response", ["code", "body"])


class TestHttpApiHandlerApp(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return WebApplication(ApiClient("http"), use_local_api=True, token="token")

    def _check_request(
        self,
        expected_response,
        resource="token",
        path="/api/experiments/123/{}",
        headers={"Content-Type": "application/json"},
    ):
        response = self.fetch(path.format(resource), method="GET", headers=headers)
        assert response.code == expected_response.code
        assert response.body == expected_response.body

    def test_valid_token_request(self):
        expected_response = Response(200, json.dumps({"token": "token"}).encode())
        self._check_request(expected_response)

    def test_valid_node_request(self):
        expected_response = Response(200, json.dumps(NODES).encode())
        self._check_request(expected_response, resource="")

    def test_invalid_experiment_id(self):
        for path in ["/api/experiments/abc/token", "/api/experiments//token"]:
            path = "/api/experiments/abc/token"
            response = self.fetch(
                path, method="GET", headers={"Content-Type": "application/json"}
            )
            assert response.code == 404

    def test_invalid_resource(self):
        resource = "invalid"
        expected_response = Response(
            404, "Invalid resource '{}'".format(resource).encode()
        )
        self._check_request(expected_response, resource=resource)


class TestHttpApiHandlerInvalidTokenApp(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return WebApplication(ApiClient("http"), use_local_api=True)

    def test_invalid_token_request(self):
        expected_response = Response(400, b"No internal token set")
        response = self.fetch(
            "/api/experiments/123/token",
            method="GET",
            headers={"Content-Type": "application/json"},
        )
        assert response.code == expected_response.code
        assert response.body == expected_response.body
