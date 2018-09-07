"""Manage command line parsers."""

import argparse

from .common import (DEFAULT_APPLICATION_HOST, DEFAULT_APPLICATION_PORT,
                     DEFAULT_AUTH_HOST, DEFAULT_AUTH_PORT,
                     DEFAULT_NODE_HOST)


def common_parser(description):
    """Return the common cli parser of all web tools."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--port', type=str, default=DEFAULT_APPLICATION_PORT,
                        help="websocket port")
    parser.add_argument('--token', type=str, default="",
                        help="token used for websocket authentication (only "
                             "used when localhost is the auth host)")
    parser.add_argument('--debug', action='store_true',
                        help="enable debug mode")
    return parser


def service_cli_parser():
    """Return the parser of the service tool."""
    parser = common_parser("Websocket service application")
    parser.add_argument('--auth-host', type=str, default=DEFAULT_AUTH_HOST,
                        help="token authentication http host")
    parser.add_argument('--auth-port', type=str, default=DEFAULT_AUTH_PORT,
                        help="token authentication http port")
    parser.add_argument('--use-local-auth', action='store_true',
                        help="Start the application http authentication"
                             "handler.")
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
    return parser
