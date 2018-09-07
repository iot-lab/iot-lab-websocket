"""iotlab-websocket client cli tests."""

import sys
import argparse
import logging
import unittest

import mock

from iotlabwebsocket.client_cli import main
from iotlabwebsocket.clients.websocket_client import WebsocketClient

LOGGER = logging.getLogger("iotlabwebsocket")

URL = "ws://{}:{}/ws/{}/{}"


@mock.patch('iotlabwebsocket.clients.websocket_client.WebsocketClient.run')
@mock.patch('iotlabwebsocket.clients.'
            'websocket_client.WebsocketClient.__init__')
@mock.patch('tornado.ioloop.IOLoop.current')
class ClientCliTest(unittest.TestCase):

    def test_main_client_cli_default(self, ioloop, init, run):
        init.return_value = None
        args = []
        main(args)

        default_url = URL.format('localhost', '8000', '', 'localhost')

        init.assert_called_with(default_url, '')
        run.assert_called_once()

    def test_main_client_cli_args(self, ioloop, init, run):
        init.return_value = None
        host = 'server_host'
        port = '8082'
        exp_id = '123'
        node = 'node-42'
        token_test = 'test_token'
        args = ['--host', host, '--port', port, '--node', node, '--id', exp_id,
                '--token', token_test]
        main(args)

        expected_url = URL.format(host, port, exp_id, node)
        init.assert_called_with(expected_url, token_test)
        run.assert_called_once()

    def test_main_client_debug(self, ioloop, init, run):
        init.return_value = None
        args = ['--debug']
        main(args)

        assert LOGGER.getEffectiveLevel() == logging.DEBUG
