"""One way websocket simple client"""

import argparse
import time
import sys
import threading
import logging

import websocket

LOGGER = logging.getLogger(__name__)


class WebsocketClient(threading.Thread):

    def __init__(self, url, verbose=False, debug=False):

        if verbose:
            websocket.enableTrace(True)
        
        if debug:
            LOGGER.setLevel(logging.INFO)

        self.key = args.key
        self.ws = websocket.WebSocketApp(url, on_open = self.on_open,
                                         on_message = self.on_message,
                                         on_error = self.on_error,
                                         on_close = self.on_close)
        # Thread management
        self._thread_init()
        self._running = threading.Event()

    def _thread_init(self):
        """ Init Thread.
        Must be called in __init__ and after stop.
        This will allow calling start-stop without re-instanciating """
        # threading.Thread init
        super(WebsocketClient, self).__init__(target=self.ws.run_forever)

    def on_message(self, ws, message):
        sys.stdout.write(message)

    def on_error(self, ws, error):
        LOGGER.error(error)
        self.stop()

    def on_close(self, ws):
        self.stop()
        logging.info("### connection closed ###")

    def on_open(self, ws):
        logging.debug("### connection opened ###")
        self.ws.send(self.key)

    def start(self):
        super(WebsocketClient, self).start()

        try:
            LOGGER.info("### listening to stdin ###")
            while True:
                message = sys.stdin.readline().strip()
                self.ws.send(message + '\n')
        except websocket.WebSocketException:
            self.stop()

    def stop(self):
        self._running.clear()
        self._thread_init()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Websocket node")
    parser.add_argument('--host', type=str, default="localhost",
                        help="Websocket host.")
    parser.add_argument('--port', type=str, default="8000",
                        help="Websocket port")
    parser.add_argument('--node', type=str, default="localhost",
                        help="node hostname")
    parser.add_argument('--key', type=str, default="key",
                        help="Key used for websocket authentication")
    parser.add_argument('--verbose', action='store_true',
                        help="Enable websocket verbose mode")
    parser.add_argument('--debug', action='store_true',
                        help="Enable debug message")
    args = parser.parse_args()
    try:
        url = "ws://{}:{}/ws/{}".format(args.host, args.port, args.node)
        ws_client = WebsocketClient(url, args.verbose, args.debug)
        ws_client.start()
    except KeyboardInterrupt:
        print("Exiting")
        ws_client.stop()
        sys.exit()
