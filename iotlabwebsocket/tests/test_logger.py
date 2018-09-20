"""iotlab-websocket logger test."""

import os.path
import logging
from logging.handlers import RotatingFileHandler

import mock

from iotlabwebsocket.logger import (setup_client_logger, setup_server_logger,
                                    LOGGER, CLIENT_LOGGER)


def test_server_empty_logger():
    logger = logging.getLogger("iotlabwebsocket")
    assert logger is LOGGER
    setup_server_logger()
    assert not logger.handlers


def test_server_file_logger(tmpdir):
    logger = logging.getLogger("iotlabwebsocket")
    assert logger is LOGGER
    log_file = os.path.join(tmpdir.strpath, 'test.log')
    setup_server_logger(log_file=log_file)
    assert len(logger.handlers) == 1

    handler = logger.handlers[0]
    assert isinstance(handler, RotatingFileHandler)

    logger.info("Test logger")
    with open(log_file, 'r') as f:
        assert "Test logger" in f.read()

    logger.removeHandler(handler)
    assert len(logger.handlers) == 0


def test_server_console_logger(capsys):
    logger = logging.getLogger("iotlabwebsocket")
    assert logger is LOGGER
    setup_server_logger(log_console=True)
    assert len(logger.handlers) == 1
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    logger.removeHandler(handler)
    assert len(logger.handlers) == 0


def test_empty_client_logger():
    logger = logging.getLogger("iotlabwebsocket-client")
    assert logger is CLIENT_LOGGER
    setup_client_logger()

    assert len(logger.handlers) == 1
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    logger.removeHandler(handler)
    assert len(logger.handlers) == 0