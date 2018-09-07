"""iotlabwebserial application command line interface"""

import logging

import tornado

from .common import LOGGER
from .web_application import WebApplication
from .parser import service_cli_parser


def main(args=None):
    """Main function of the web application."""
    args = service_cli_parser().parse_args(args)
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)
    app = WebApplication(args.auth_host, args.auth_port, token=args.token)
    try:
        app.listen(args.port)
        LOGGER.info('Application started, listening on port %s', args.port)
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        LOGGER.debug('Shuting down service')
        app.stop()
        tornado.ioloop.IOLoop.current().stop()
