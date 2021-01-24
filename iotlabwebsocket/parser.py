"""Manage command line parsers."""

import os
import argparse

from . import DEFAULT_APPLICATION_PORT, DEFAULT_API_HOST, DEFAULT_API_PORT


def service_cli_parser():
    """Return the parser of the service tool."""
    parser = argparse.ArgumentParser(description="Websocket service application")
    parser.add_argument(
        "--port",
        type=str,
        default=DEFAULT_APPLICATION_PORT,
        help="websocket server port",
    )
    parser.add_argument(
        "--token",
        type=str,
        default="",
        help="token used for websocket authentication (only "
        "used when localhost is the auth host)",
    )
    parser.add_argument(
        "--api-protocol",
        default="https",
        nargs="?",
        choices=["https", "http"],
        help="protocol used to access the REST API",
    )
    parser.add_argument(
        "--api-host", type=str, default=DEFAULT_API_HOST, help="REST API server host"
    )
    parser.add_argument(
        "--api-port", type=str, default=DEFAULT_API_PORT, help="REST API server port"
    )
    parser.add_argument(
        "--api-user",
        type=str,
        default=os.getenv("API_USER", ""),
        help="username used to connect to the REST API",
    )
    parser.add_argument(
        "--api-password",
        type=str,
        default=os.getenv("API_PASSWORD", ""),
        help="password used to connect to the REST API",
    )
    parser.add_argument(
        "--use-local-api",
        action="store_true",
        help="Start and use the local API handler.",
    )
    parser.add_argument(
        "--log-file", type=str, default=None, help="Absolute path of the log file"
    )
    parser.add_argument(
        "--log-console", action="store_true", help="Print debug messages to console."
    )
    return parser
