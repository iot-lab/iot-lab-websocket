"""iotlab-websocket client cli tests."""

import sys
import argparse
import logging
import unittest

import tornado

import mock
import pytest

from iotlabwebsocket.logger import CLIENT_LOGGER
from iotlabwebsocket.client_cli import main
from iotlabwebsocket.clients.websocket_client import WebsocketClient

URL = "{}://{}:{}/ws/{}/{}/{}/serial"


@mock.patch('iotlabwebsocket.api.ApiClient.fetch_token_sync')
@mock.patch('iotlabwebsocket.clients.websocket_client.WebsocketClient.run')
@mock.patch('iotlabwebsocket.clients.'
            'websocket_client.WebsocketClient.__init__')
@mock.patch('tornado.ioloop.IOLoop.current')
class ClientCliTest(unittest.TestCase):

    def test_main_client_cli_default(self, ioloop, init, run, fetch):
        init.return_value = None
        fetch.return_value = 'token'
        args = []
        main(args)

        default_url = URL.format('wss', 'localhost', '8000',
                                 'local', '', 'localhost')

        init.assert_called_with(default_url, 'token')
        fetch.assert_called_with("")
        run.assert_called_once()
        ioloop.assert_called_once()  # for the start

    def test_main_client_cli_args(self, ioloop, init, run, fetch):
        init.return_value = None
        host = 'server_host'
        port = '8082'
        exp_id = '123'
        node = 'node-42'
        site = 'site'
        token_test = 'test_token'
        args = ['--host', host, '--port', port, '--node',
                '{}.{}'.format(node, site), '--exp-id', exp_id,
                '--token', token_test]
        main(args)

        expected_url = URL.format('wss', host, port, 'site', exp_id, node)
        init.assert_called_with(expected_url, token_test)
        assert fetch.call_count == 0
        run.assert_called_once()
        ioloop.assert_called_once()  # for the start
        assert CLIENT_LOGGER.getEffectiveLevel() == logging.ERROR

    def test_main_client_insecure(self, ioloop, init, run, fetch):
        init.return_value = None
        fetch.return_value = 'token'
        args = ['--insecure']
        main(args)

        insecure_url = URL.format('ws', 'localhost', '8000',
                                  'local', '', 'localhost')

        init.assert_called_with(insecure_url, fetch.return_value)
        run.assert_called_once()
        ioloop.assert_called_once()  # for the start
        assert CLIENT_LOGGER.getEffectiveLevel() == logging.ERROR

    @mock.patch('iotlabwebsocket.client_cli.setup_client_logger')
    def test_main_client_logger(self, setup_logger, ioloop, init, fetch, run):
        init.return_value = None
        args = ['--debug']
        main(args)

        ioloop.assert_called_once()  # for the start
        setup_logger.assert_called_once()

    def test_main_client_exit(self, ioloop, init, run, fetch):
        init.return_value = None
        run.side_effect = KeyboardInterrupt
        args = []
        main(args)

        ioloop.assert_called_once()  # for the stop


def test_invalid_node(capsys):
    main(['--node', 'invalid-node'])
    out, _ = capsys.readouterr()
    assert "Invalid node name" in out


def test_cannot_fetch(capsys):
    with mock.patch('tornado.httpclient.HTTPClient.fetch') as fetch:
        fetch.side_effect = tornado.httpclient.HTTPClientError(42)
        main(['--node', 'node.local'])
        out, _ = capsys.readouterr()
        assert "Cannot fetch token from API" in out
