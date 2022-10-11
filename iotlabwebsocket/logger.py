"""Common variables module."""

import sys
import logging
from logging.handlers import RotatingFileHandler

LOGGER = logging.getLogger("iotlabwebsocket")
LOGGER.setLevel(logging.DEBUG)


def setup_server_logger(log_file=None, log_console=False):
    """Setup logger for client application."""
    formatter = logging.Formatter(
        "%(asctime)-15s %(levelname)-7s %(filename)20s:%(lineno)-3d %(message)s"
    )
    if log_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        LOGGER.addHandler(console_handler)

    if log_file is not None:
        server = RotatingFileHandler(log_file, "a", maxBytes=1000000, backupCount=1)
        server.setFormatter(formatter)
        server.setLevel(logging.DEBUG)
        LOGGER.addHandler(server)
