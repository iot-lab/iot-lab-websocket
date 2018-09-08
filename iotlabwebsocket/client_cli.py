"""websocket client command line interface"""

import logging

import tornado

from .logger import setup_client_logger
from .logger import CLIENT_LOGGER as LOGGER
from .clients.websocket_client import WebsocketClient
from .parser import client_cli_parser


def main(args=None):
    """Main function of the websocket client cli."""
    args = client_cli_parser().parse_args(args)
    if not args.debug:
        LOGGER.setLevel(logging.ERROR)
    setup_client_logger()
    try:
        protocol = 'wss'
        if args.insecure:
            protocol = 'ws'
        url = "{}://{}:{}/ws/{}/{}/{}".format(
            protocol, args.host, args.port, args.exp_id, args.node, args.type)
        ws_client = WebsocketClient(url, args.token)
        ws_client.run()
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        LOGGER.debug("Exiting")
        tornado.ioloop.IOLoop.current().stop()
