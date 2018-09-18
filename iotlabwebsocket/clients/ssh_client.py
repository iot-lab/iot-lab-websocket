"""SSH client"""

import re
import sys
import time
import paramiko

import tornado
from tornado import gen

from ..logger import LOGGER

END_STDOUT = 'End of stdout buffer. Exit'


class SSHClient(object):
    # pylint:disable=too-few-public-methods
    """Class that connects to a websocket server while listening to stdin."""

    def __init__(self):
        self.host = None
        self.username = None
        self.on_data = None
        self.on_close = None
        self._ssh = None

    @property
    def ready(self):
        return self._ssh is not None

    @gen.coroutine
    def _connect(self, host):
        LOGGER.debug("Connect to HOST %s via SSH", host)
        self._ssh = paramiko.SSHClient()
        self._ssh.load_system_host_keys()
        self._ssh.connect(hostname=host, username='root')
        self.channel = self._ssh.get_transport().open_session()
        self.channel.get_pty()
        self.channel.invoke_shell()
        self.stdin = self.channel.makefile('wb')
        self.stdout = self.channel.makefile('r')
        LOGGER.debug("SSH connection to '%s' opened.", host)

    @gen.coroutine
    def start(self, host, on_data, on_close):
        """Connect and listen to a SSH server."""
        self.host = host
        self.on_data = on_data
        self.on_close = on_close
        # Connect to SSH host
        yield self._connect(host)

    @gen.coroutine
    def send(self, command):
        """Send data via the SSH connection."""
        if not self.ready:
            return
        command = command.decode()
        LOGGER.debug("Send command '%s' to SSH connection", command)
        # self._listen_channel()
        self.stdin.write(command + '\n')
        echo_cmd = 'echo {} $?'.format(END_STDOUT)
        self.stdin.write(echo_cmd + '\n')
        self.stdin.flush()
        shout = []
        for line in self.stdout:
            if line.startswith(command) or line.startswith(echo_cmd):
                shout = []
            elif line.startswith(END_STDOUT):
                exit_status = int(line.rsplit(maxsplit=1)[1])
                if exit_status:
                    shout = []
                break
            else:
                shout.append(re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
                             .sub('', line)
                             .replace('\b', '').replace('\r', ''))
        
        if shout and echo_cmd in shout[-1]:
            shout.pop()
        # if shout and command in shout[0]:
        #     shout.pop(0)

        # LOGGER.debug(shout)
        for line in shout:
            # LOGGER.debug("Reply line %s", line)
            yield self.on_data(self.host, line)

    def stop(self):
        if self.ready:
            LOGGER.debug("Stopping SSH connection")
            self._ssh.close()
            self._ssh = None
        elif self.host is not None:
            self.on_close(self.host)
