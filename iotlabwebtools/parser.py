"""Manage command line parsers."""

import argparse

DEFAULT_AUTH_URL = "http://localhost:8000/experiments"


def common_parser(description):
    """Return the common cli parser of all web tools."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--debug', action='store_true',
                        help="Enable debug mode")
    return parser


def service_cli_parser():
    """Return the parser of the service tool."""
    parser = common_parser("Websocket service application")
    parser.add_argument('--port', type=str, default="8000",
                        help="Listening port")
    parser.add_argument('--auth-url', type=str, default=DEFAULT_AUTH_URL,
                        help="Token authentication URL")
    return parser


def websocket_cli_parser():
    """Return the cli parser of the websocket client."""
    parser = common_parser("Websocket client")
    parser.add_argument('--host', type=str, default="localhost",
                        help="Websocket host.")
    parser.add_argument('--port', type=str, default="8000",
                        help="Websocket port")
    parser.add_argument('--node', type=str, default="localhost",
                        help="node hostname")
    parser.add_argument('--id', type=str, default="",
                        help="experiment id associated to node")
    parser.add_argument('--token', type=str, default="",
                        help="token used for websocket authentication")
    return parser
