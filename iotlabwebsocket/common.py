"""Common variables module."""

import logging

logging.basicConfig(format='%(asctime)-15s %(levelname)-7s '
                           '%(filename)20s:%(lineno)-3d %(message)s')
LOGGER = logging.getLogger("iotlabwebsocket")
LOGGER.setLevel(logging.INFO)

DEFAULT_APPLICATION_HOST = 'localhost'
DEFAULT_APPLICATION_PORT = '8000'
DEFAULT_AUTH_HOST = 'localhost'
DEFAULT_AUTH_PORT = '8000'
DEFAULT_NODE_HOST = 'localhost'
