"""iotlabwebsocket service cli tests."""

import os
import os.path
import unittest

import mock

from iotlabwebsocket.api import ApiClient
from iotlabwebsocket.service_cli import main


@mock.patch("iotlabwebsocket.web_application.WebApplication.stop")
@mock.patch("iotlabwebsocket.web_application.WebApplication.listen")
@mock.patch("iotlabwebsocket.web_application.WebApplication.__init__")
@mock.patch("tornado.ioloop.IOLoop.instance")
class ServiceCliTest(unittest.TestCase):
    def test_main_service_cli_default(self, ioloop, init, listen, stop_app):
        init.return_value = None
        args = []

        default_api = ApiClient("https")
        main(args)

        ioloop.assert_called_once()  # for the start
        args, kwargs = init.call_args
        assert len(args) == 1
        assert args[0] == default_api
        assert kwargs == dict(use_local_api=False, token="")
        listen.assert_called_with("8000")

    def test_main_service_cli_args(self, ioloop, init, listen, stop_app):
        init.return_value = None
        api_host_test = "testhost"
        api_port_test = "8080"
        api_test = ApiClient("https", api_host_test, api_port_test, "", "")
        port_test = "8082"
        token_test = "test_token"
        args = [
            "--api-host",
            api_host_test,
            "--api-port",
            api_port_test,
            "--use-local-api",
            "--token",
            token_test,
            "--port",
            port_test,
        ]
        main(args)

        ioloop.assert_called_once()  # for the start
        args, kwargs = init.call_args
        assert len(args) == 1
        assert args[0] == api_test
        assert kwargs == dict(use_local_api=True, token=token_test)
        listen.assert_called_with(port_test)

    def test_main_service_http(self, ioloop, init, listen, stop_app):
        init.return_value = None
        args = ["--api-protocol", "http"]

        http_api = ApiClient("http")
        main(args)

        ioloop.assert_called_once()  # for the start
        args, kwargs = init.call_args
        assert len(args) == 1
        assert args[0] == http_api
        assert kwargs == dict(use_local_api=False, token="")
        listen.assert_called_with("8000")

    @mock.patch("iotlabwebsocket.service_cli.setup_server_logger")
    def test_main_service_logging(self, setup_logger, ioloop, init, listen, stop_app):
        init.return_value = None
        log_file_test = os.path.join("/tmp/test.log")
        args = ["--log-file", log_file_test, "--log-console"]
        main(args)

        ioloop.assert_called_once()  # for the start
        setup_logger.assert_called_with(log_file=log_file_test, log_console=True)

    def test_main_service_exit(self, ioloop, init, listen, stop_app):
        init.return_value = None
        listen.side_effect = KeyboardInterrupt
        args = []
        main(args)

        ioloop.assert_called_once()  # for the stop

    def test_main_service_env(self, ioloop, init, listen, stop_app):
        init.return_value = None
        api_host_test = "testhost"
        api_port_test = "8080"
        username = "aaaa"
        password = "bbbb"
        api_test = ApiClient("https", api_host_test, api_port_test, username, password)
        port_test = "8082"
        token_test = "test_token"
        args = [
            "--api-host",
            api_host_test,
            "--api-port",
            api_port_test,
            "--use-local-api",
            "--token",
            token_test,
            "--port",
            port_test,
        ]
        os.environ["API_USER"] = username
        os.environ["API_PASSWORD"] = password
        main(args)

        # Cleanup
        os.environ.pop("API_USER")
        os.environ.pop("API_PASSWORD")

        ioloop.assert_called_once()  # for the start
        args, kwargs = init.call_args
        assert len(args) == 1
        assert args[0] == api_test
        assert kwargs == dict(use_local_api=True, token=token_test)
        listen.assert_called_with(port_test)
