"""websocket client command line interface"""

# pylint:disable=superfluous-parens

import logging

import tornado

from .logger import setup_client_logger
from .logger import CLIENT_LOGGER as LOGGER
from .clients.websocket_client import WebsocketClient
from .api import ApiClient
from .parser import client_cli_parser


def _parse_node(node_fqdn):
    node_split = node_fqdn.split('.')

    if len(node_split) < 2:
        raise ValueError("Invalid node name '{}'. Node name should use the "
                         "following scheme: <hostname>.<site>"
                         .format(node_fqdn))
    return node_split[:2]


def main(args=None):
    """Main function of the websocket client cli."""
    args = client_cli_parser().parse_args(args)
    if not args.debug:
        LOGGER.setLevel(logging.ERROR)
    setup_client_logger()
    try:
        node, site = _parse_node(args.node)
        token = args.token
        if not args.token:
            # Fetch token from API
            api = ApiClient(args.api_protocol, args.api_host, args.api_port,
                            args.api_user, args.api_password)
            token = api.fetch_token_sync(args.exp_id)  # Blocking call
        protocol = 'wss'
        if args.insecure:
            protocol = 'ws'
        ws_url = "{}://{}:{}/ws/{}/{}/{}/{}".format(
            protocol, args.host, args.port, site, args.exp_id, node, args.type)
        ws_client = WebsocketClient(ws_url, token)
        ws_client.run()
        tornado.ioloop.IOLoop.instance().start()
    except tornado.httpclient.HTTPClientError as exc:
        print("Cannot fetch token from API: {}".format(exc))
    except ValueError as exc:
        print("Error: {}".format(exc))
    except KeyboardInterrupt:
        LOGGER.debug("Exiting")
    finally:
        tornado.ioloop.IOLoop.instance().stop()
