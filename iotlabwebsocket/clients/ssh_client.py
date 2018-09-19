"""SSH client"""

import tornado
from tornado import gen

import paramiko

from ..logger import LOGGER


class SSHClient(object):
    # pylint:disable=too-few-public-methods
    """Class that connects to a websocket server while listening to stdin."""

    def __init__(self, host, on_data, on_close):
        self.host = host
        self.on_data = on_data
        self.on_close = on_close
        self.username = 'root'
        self._ssh = None
        self._channel = None
        self._listen = False

    @property
    def ready(self):
        """Check if SSH connection is ready."""
        return self._ssh is not None

    @gen.coroutine
    def _connect(self):
        LOGGER.debug("Connect to host %s via SSH", self.host)
        self._ssh = paramiko.SSHClient()
        try:
            self._ssh.load_system_host_keys()
            self._ssh.connect(hostname=self.host, username=self.username)
            self._channel = self._ssh.get_transport().open_session()
            self._channel.get_pty()
            self._channel.invoke_shell()
        except paramiko.ssh_exception.SSHException:
            LOGGER.error("Cannot connect via SSH to %s", self.host)
            raise gen.Return(False)
        LOGGER.debug("SSH connection to '%s' opened.", self.host)
        raise gen.Return(True)

    @gen.coroutine
    def _listen_channel(self):
        while self._channel.recv_ready():
            data = self._channel.recv(1)
            self.on_data(self, data)

        if self._listen:
            # Avoid busy loops with 100% CPU usage
            yield gen.sleep(0.1)

            ioloop = tornado.ioloop.IOLoop.current()
            ioloop.spawn_callback(self._listen_channel)

    @gen.coroutine
    def start(self):
        """Connect and listen to a SSH server."""
        # Connect to SSH host
        connected = yield self._connect()
        if not connected:
            raise gen.Return(False)

        self._listen = True
        ioloop = tornado.ioloop.IOLoop.current()
        ioloop.spawn_callback(self._listen_channel)
        raise gen.Return(True)

    def send(self, command):
        """Send data via the SSH connection."""
        if not self.ready:
            return
        self._channel.send(command)
        # Handle exit in ssh as closing command for the websocket
        if command == b'exit\n':
            LOGGER.debug("Exit command: stopping SSH connection")
            self.on_close(self)

    def stop(self):
        """Stop the SSH connection."""
        if self.ready:
            LOGGER.debug("Stopping SSH connection")
            self._ssh.close()
            self._ssh = None
            self._listen = False
        elif self.host is not None:
            self.on_close(self)
