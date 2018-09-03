"""iotlabwebserial helper functions."""

import logging
import signal
from functools import partial

import tornado

LOGGER = logging.getLogger("iotlabwebserial")


def signal_handler(server, sig, frame):
    # pylint:disable=unused-argument
    """Triggered when a signal is received from system."""
    ioloop = tornado.ioloop.IOLoop.instance()

    def shutdown():
        """Force server and ioloop shutdown."""
        tornado.ioloop.IOLoop.current().stop()
        if server is not None:
            server.stop()
        ioloop.stop()

    ioloop.add_callback_from_signal(shutdown)
    LOGGER.debug('Shuting down server (caught signal: %s)', str(sig))


def start_application(app, port):
    """Start a tornado application."""
    server = app.listen(port)
    signal.signal(signal.SIGTERM, partial(signal_handler, server))
    signal.signal(signal.SIGINT, partial(signal_handler, server))
