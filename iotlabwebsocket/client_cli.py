"""websocket client command line interface"""

import json
import logging

import tornado

from .logger import setup_client_logger
from .logger import CLIENT_LOGGER as LOGGER
from .clients.websocket_client import WebsocketClient
from .api import ApiHelper
from .parser import client_cli_parser


def main(args=None):
    """Main function of the websocket client cli."""
    args = client_cli_parser().parse_args(args)
    if not args.debug:
        LOGGER.setLevel(logging.ERROR)
    setup_client_logger()
    try:
        # Fetch node list
        api = ApiHelper(args.api_protocol, args.api_host, args.api_port,
                        args.api_user, args.api_password)
        nodes_url = '{}/{}/nodes'.format(api.url, args.exp_id)
        http_client = tornado.httpclient.HTTPClient()
        request = tornado.httpclient.HTTPRequest(nodes_url,
                                                 auth_username=api.username,
                                                 auth_password=api.password)
        request.headers["Content-Type"] = "application/json"
        response = http_client.fetch(request).buffer.read()
        for item in json.loads(response)['items']:
            print('node:', item['network_address'])

        protocol = 'wss'
        if args.insecure:
            protocol = 'ws'
        ws_url = "{}://{}:{}/ws/{}/{}/{}".format(
            protocol, args.host, args.port, args.exp_id, args.node, args.type)
        ws_client = WebsocketClient(ws_url, args.token)
        ws_client.run()
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        LOGGER.debug("Exiting")
        tornado.ioloop.IOLoop.current().stop()
