"""iotlabwebserial application command line interface"""

import signal
import logging
from functools import partial

import tornado

from .web_application import WebApplication
from .parser import service_cli_parser

logging.basicConfig(format='%(asctime)-15s %(levelname)-7s '
                           '%(filename)20s:%(lineno)-3d %(message)s')
LOGGER = logging.getLogger("iotlabwebtools")
LOGGER.setLevel(logging.INFO)


def signal_handler(server, app, sig, frame):
    # pylint:disable=unused-argument
    """Triggered when a signal is received from system."""
    ioloop = tornado.ioloop.IOLoop.instance()

    def shutdown():
        """Force server and ioloop shutdown."""
        app.stop()
        tornado.ioloop.IOLoop.current().stop()
        if server is not None:
            server.stop()
        ioloop.stop()

    ioloop.add_callback_from_signal(shutdown)
    LOGGER.debug('Shuting down server (caught signal: %s)', str(sig))


def start_application(app, port):
    """Start a tornado application."""
    server = app.listen(port)
    signal.signal(signal.SIGTERM, partial(signal_handler, server, app))
    signal.signal(signal.SIGINT, partial(signal_handler, server, app))


def main(args=None):
    """Main function of the web application."""
    args = args or service_cli_parser().parse_args()
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)
    start_application(WebApplication(auth_url=args.auth_url), args.port)
    LOGGER.info('Application started, listening on port %s', args.port)

    tornado.ioloop.IOLoop.current().start()
