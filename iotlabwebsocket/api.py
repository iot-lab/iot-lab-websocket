"""Helper module for API url and authentication."""

API_URL = "{}://{}:{}/api/experiments"


class ApiHelper(object):
    """Class that store information about the REST API."""

    def __init__(self, protocol, host, port, username, password):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    @property
    def url(self):
        """Returns the base URL for experiments in the API."""
        return API_URL.format(self.protocol, self.host, self.port)
