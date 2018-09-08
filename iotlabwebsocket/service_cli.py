"""iotlabwebserial application command line interface"""

import tornado

from .logger import LOGGER, setup_server_logger
from .web_application import WebApplication
from .parser import service_cli_parser


def main(args=None):
    """Main function of the web application."""
    args = service_cli_parser().parse_args(args)
    setup_server_logger(log_file=args.log_file, log_console=args.log_console)
    app = WebApplication(args.auth_host, args.auth_port,
                         use_local_auth=args.use_local_auth, token=args.token)
    try:
        app.listen(args.port)
        LOGGER.info('Application started, listening on port %s', args.port)
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        LOGGER.debug('Shuting down service')
        app.stop()
        tornado.ioloop.IOLoop.current().stop()
