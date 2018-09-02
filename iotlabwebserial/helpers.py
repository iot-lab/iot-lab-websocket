
import logging
import signal
from functools import partial

import tornado

from tornado.options import options

LOGGER = logging.getLogger("iotlabwebserial")


def signal_handler(server, app_close, sig, frame):
    """Triggered when a signal is received from system."""
    ioloop = tornado.ioloop.IOLoop.instance()

    def shutdown():
        """Force server and ioloop shutdown."""
        LOGGER.debug('Shuting down server')
        tornado.ioloop.IOLoop.current().stop()
        if app_close is not None:
            app_close()
        if server is not None:
            server.stop()
        ioloop.stop()

    LOGGER.warning('Caught signal: %s', sig)
    ioloop.add_callback_from_signal(shutdown)


def start_application(app, port):
    """Start a tornado application."""
    server = app.listen(port)
    signal.signal(signal.SIGTERM, partial(signal_handler, server, None))
    signal.signal(signal.SIGINT, partial(signal_handler, server, None))
    LOGGER.debug('Application started, listening on port {}'.format(port))
