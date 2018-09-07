"""iotlabwebsocket service cli tests."""

import sys
import argparse
import logging
import unittest

import mock

from iotlabwebsocket.service_cli import main
from iotlabwebsocket.web_application import WebApplication, DEFAULT_AUTH_URL

LOGGER = logging.getLogger("iotlabwebsocket")


@mock.patch('iotlabwebsocket.web_application.WebApplication.stop')
@mock.patch('iotlabwebsocket.web_application.WebApplication.listen')
@mock.patch('iotlabwebsocket.web_application.WebApplication.__init__')
@mock.patch('tornado.ioloop.IOLoop.current')
class ServiceCliTest(unittest.TestCase):

    def test_main_service_cli_default(self, ioloop, init, listen, stop_app):
        init.return_value = None
        args = []
        main(args)

        # start.assert_called_once()
        init.assert_called_with(auth_url=DEFAULT_AUTH_URL, token='')
        listen.assert_called_with('8000')

    def test_main_service_cli_args(self, ioloop, init, listen, stop_app):
        init.return_value = None
        auth_url_test = 'http://testhost/test'
        port_test = '8082'
        token_test = 'test_token'
        args = ['--auth-url', auth_url_test, '--token', token_test,
                '--port', port_test]
        main(args)

        # start.assert_called_once()
        init.assert_called_with(auth_url=auth_url_test, token=token_test)
        listen.assert_called_with(port_test)

    def test_main_debug(self, ioloop, init, listen, stop_app):
        init.return_value = None
        args = ['--debug']
        main(args)

        assert LOGGER.getEffectiveLevel() == logging.DEBUG
