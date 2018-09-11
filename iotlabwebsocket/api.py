"""Client class for REST API."""

import json

import tornado
from tornado import gen

from . import DEFAULT_API_HOST, DEFAULT_API_PORT

API_URL = "{}://{}:{}/api/experiments"


class ApiClient(object):
    """Class that store information about the REST API."""

    def __init__(self, protocol, host=DEFAULT_API_HOST, port=DEFAULT_API_PORT,
                 username="", password=""):
        # pylint:disable=too-many-arguments
        self.protocol = protocol
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def __eq__(self, other):
        return (self.protocol == other.protocol and
                self.host == other.host and
                self.port == other.port and
                self.username == other.username and
                self.password == other.password)

    @property
    def url(self):
        """Returns the base URL for experiments in the API."""
        return API_URL.format(self.protocol, self.host, self.port)

    @staticmethod
    def _fetch_sync(request):
        http_client = tornado.httpclient.HTTPClient()
        request.headers["Content-Type"] = "application/json"
        response = http_client.fetch(request).buffer.read()
        return response

    @staticmethod
    @gen.coroutine
    def _fetch_async(request):
        http_client = tornado.httpclient.AsyncHTTPClient()
        request.headers["Content-Type"] = "application/json"
        response = yield http_client.fetch(request)
        raise gen.Return(response.buffer.read())

    def _request(self, exp_id, resource):
        nodes_url = '{}/{}/{}'.format(self.url, exp_id, resource)
        kwargs = {}
        if self.username and self.password:
            kwargs.update({'auth_username': self.username,
                           'auth_password': self.password})
        return tornado.httpclient.HTTPRequest(nodes_url, **kwargs)

    @staticmethod
    def _parse_nodes_response(response):
        nodes = []
        for item in json.loads(response)['items']:
            nodes.append(item['network_address'])
        return nodes

    def fetch_nodes_sync(self, exp_id):
        """Fetch the list of nodes using a synchronous call."""
        response = ApiClient._fetch_sync(self._request(exp_id, 'nodes'))
        return ApiClient._parse_nodes_response(response.decode())

    @gen.coroutine
    def fetch_nodes_async(self, exp_id):
        """Fetch the list of nodes using an asynchronous call."""
        response = yield ApiClient._fetch_async(self._request(exp_id, 'nodes'))
        raise gen.Return(ApiClient._parse_nodes_response(response.decode()))

    def fetch_token_sync(self, exp_id):
        """Fetch the experiment token using a synchronous call."""
        response = ApiClient._fetch_sync(self._request(exp_id, 'token'))
        return json.loads(response.decode())['token']

    @gen.coroutine
    def fetch_token_async(self, exp_id):
        """Fetch the experiment token using an asynchronous call."""
        response = yield ApiClient._fetch_async(self._request(exp_id, 'token'))
        raise gen.Return(json.loads(response.decode())['token'])
