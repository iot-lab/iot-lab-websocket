"""iotlabwebsocket service cli tests."""

import sys
import argparse
import logging
import unittest

import mock

from iotlabwebsocket.common import (DEFAULT_AUTH_HOST, DEFAULT_AUTH_PORT,
                                    LOGGER)
from iotlabwebsocket.service_cli import main
from iotlabwebsocket.web_application import WebApplication, AUTH_URL


@mock.patch('iotlabwebsocket.web_application.WebApplication.stop')
@mock.patch('iotlabwebsocket.web_application.WebApplication.listen')
@mock.patch('iotlabwebsocket.web_application.WebApplication.__init__')
@mock.patch('tornado.ioloop.IOLoop.current')
class ServiceCliTest(unittest.TestCase):

    def test_main_service_cli_default(self, ioloop, init, listen, stop_app):
        init.return_value = None
        args = []
        main(args)

        ioloop.assert_called_once()  # for the start
        init.assert_called_with(DEFAULT_AUTH_HOST, DEFAULT_AUTH_PORT, token='')
        listen.assert_called_with('8000')

    def test_main_service_cli_args(self, ioloop, init, listen, stop_app):
        init.return_value = None
        auth_host_test = 'testhost'
        auth_port_test = '8080'
        port_test = '8082'
        token_test = 'test_token'
        args = ['--auth-host', auth_host_test, '--auth-port', auth_port_test,
                '--token', token_test, '--port', port_test]
        main(args)

        ioloop.assert_called_once()  # for the start
        init.assert_called_with(auth_host_test, auth_port_test,
                                token=token_test)
        listen.assert_called_with(port_test)

    def test_main_service_debug(self, ioloop, init, listen, stop_app):
        init.return_value = None
        args = ['--debug']
        main(args)

        ioloop.assert_called_once()  # for the start
        assert LOGGER.getEffectiveLevel() == logging.DEBUG

    def test_main_service_exit(self, ioloop, init, listen, stop_app):
        init.return_value = None
        listen.side_effect = KeyboardInterrupt
        args = []
        main(args)

        ioloop.assert_called_once()  # for the stop
