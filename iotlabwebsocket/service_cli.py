"""iotlabwebserial application command line interface"""

import signal
import logging
from functools import partial

import tornado

from .web_application import WebApplication
from .parser import service_cli_parser

logging.basicConfig(format='%(asctime)-15s %(levelname)-7s '
                           '%(filename)20s:%(lineno)-3d %(message)s')
LOGGER = logging.getLogger("iotlabwebsocket")
LOGGER.setLevel(logging.INFO)


def main(args=None):
    """Main function of the web application."""
    args = service_cli_parser().parse_args(args)
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)
    app = WebApplication(auth_url=args.auth_url, token=args.token)
    try:
        app.listen(args.port)
        LOGGER.info('Application started, listening on port %s', args.port)
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        LOGGER.debug('Shuting down service')
        app.stop()
        tornado.ioloop.IOLoop.current().stop()
