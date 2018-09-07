"""websocket client command line interface"""

import sys
import logging

import tornado

from .clients.websocket_client import WebsocketClient
from .parser import client_cli_parser

logging.basicConfig(format='%(asctime)-15s %(filename)s:%(lineno)d '
                           '%(levelname)-5s %(message)s')
LOGGER = logging.getLogger("iotlabwebsocket")


def main(args=None):
    """Main function of the websocket client cli."""
    args = client_cli_parser().parse_args(args)
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)

    try:
        url = "ws://{}:{}/ws/{}/{}/{}".format(
            args.host, args.port, args.id, args.node, args.type)
        ws_client = WebsocketClient(url, args.token)
        ws_client.run()
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        LOGGER.info("Exiting")
        tornado.ioloop.IOLoop.current().stop()
        sys.exit()
