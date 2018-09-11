"""Manage command line parsers."""

import argparse

from . import (DEFAULT_APPLICATION_HOST, DEFAULT_APPLICATION_PORT,
               DEFAULT_API_HOST, DEFAULT_API_PORT, DEFAULT_NODE_HOST)


def common_parser(description):
    """Return the common cli parser of all web tools."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--port', type=str, default=DEFAULT_APPLICATION_PORT,
                        help="websocket server port")
    parser.add_argument('--token', type=str, default="",
                        help="token used for websocket authentication (only "
                             "used when localhost is the auth host)")
    parser.add_argument('--api-protocol', default="https", nargs='?',
                        choices=['https', 'http'],
                        help="protocol used to access the REST API")
    parser.add_argument('--api-host', type=str, default=DEFAULT_API_HOST,
                        help="REST API server host")
    parser.add_argument('--api-port', type=str, default=DEFAULT_API_PORT,
                        help="REST API server port")
    parser.add_argument('--api-user', type=str, default="",
                        help="username used to connect to the REST API")
    parser.add_argument('--api-password', type=str, default="",
                        help="password used to connect to the REST API")
    return parser


def service_cli_parser():
    """Return the parser of the service tool."""
    parser = common_parser("Websocket service application")
    parser.add_argument('--use-local-api', action='store_true',
                        help="Start and use the local API handler.")
    parser.add_argument('--log-file', type=str, default=None,
                        help="Absolute path of the log file")
    parser.add_argument('--log-console', action='store_true',
                        help="Print debug messages to console.")
    return parser


def client_cli_parser():
    """Return the cli parser of the websocket client."""
    parser = common_parser("Websocket client")
    parser.add_argument('--host', type=str, default=DEFAULT_APPLICATION_HOST,
                        help="websocket host")
    parser.add_argument('--node', type=str, default=DEFAULT_NODE_HOST,
                        help="node hostname")
    parser.add_argument('--exp-id', type=str, default="",
                        help="experiment id associated to node")
    parser.add_argument('--type', default="serial", nargs='?',
                        choices=['serial'],
                        help="the type of connection (only serial supported "
                             "for the moment)")
    parser.add_argument('--insecure', action='store_true',
                        help="connect to websocket host using insecure "
                             "protocol (ws)")
    parser.add_argument('--debug', action='store_true',
                        help="enable debug mode")
    return parser
