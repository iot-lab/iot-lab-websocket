"""iotlabwebserial application command line interface"""

import tornado

from .logger import LOGGER, setup_server_logger
from .web_application import WebApplication
from .api import ApiClient
from .parser import service_cli_parser


def main(args=None):
    """Main function of the web application."""
    args = service_cli_parser().parse_args(args)
    setup_server_logger(log_file=args.log_file, log_console=args.log_console)
    api = ApiClient(
        args.api_protocol,
        args.api_host,
        args.api_port,
        args.api_user,
        args.api_password,
    )
    app = WebApplication(api, use_local_api=args.use_local_api, token=args.token)
    try:
        app.listen(args.port)
        LOGGER.info(f"Application started, listening on port {args.port}")
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        LOGGER.debug("Shuting down service")
        app.stop()
        tornado.ioloop.IOLoop.instance().stop()
