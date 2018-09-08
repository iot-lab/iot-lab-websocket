"""iotlabwebsocket service cli tests."""

import os.path
import sys
import argparse
import logging
import unittest

import mock

from iotlabwebsocket import DEFAULT_AUTH_HOST, DEFAULT_AUTH_PORT
from iotlabwebsocket.logger import LOGGER
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
        init.assert_called_with(DEFAULT_AUTH_HOST, DEFAULT_AUTH_PORT,
                                use_local_auth=False, token='')
        listen.assert_called_with('8000')

    def test_main_service_cli_args(self, ioloop, init, listen, stop_app):
        init.return_value = None
        auth_host_test = 'testhost'
        auth_port_test = '8080'
        port_test = '8082'
        token_test = 'test_token'
        args = ['--auth-host', auth_host_test, '--auth-port', auth_port_test,
                '--use-local-auth', '--token', token_test, '--port', port_test]
        main(args)

        ioloop.assert_called_once()  # for the start
        init.assert_called_with(auth_host_test, auth_port_test,
                                use_local_auth=True, token=token_test)
        listen.assert_called_with(port_test)

    @mock.patch('iotlabwebsocket.service_cli.setup_server_logger')
    def test_main_service_logging(self, setup_logger, ioloop, init, listen,
                                  stop_app):
        init.return_value = None
        log_file_test = os.path.join('/tmp/test.log')
        args = ['--log-file', log_file_test, '--log-console']
        main(args)

        ioloop.assert_called_once()  # for the start
        setup_logger.assert_called_with(log_file=log_file_test,
                                        log_console=True)

    def test_main_service_exit(self, ioloop, init, listen, stop_app):
        init.return_value = None
        listen.side_effect = KeyboardInterrupt
        args = []
        main(args)

        ioloop.assert_called_once()  # for the stop
