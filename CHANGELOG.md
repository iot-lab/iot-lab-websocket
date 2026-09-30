Changelog
=========

Unreleased
----------

+ Disconnect websocket clients with more than 1 MB of node output pending

Version 0.5.0
-------------

+ Accept the websockets opened together for an experiment with one API
  request for its token and one for its nodes, kept 30 seconds
+ Send up to 50 API requests at the same time, and the token and nodes
  requests of a websocket together
+ Compare websocket tokens in constant time
+ Add a benchmark of websocket connections opened together
+ Require Python 3.10+, package with pyproject.toml, run on Python 3.13 in Docker
+ Use native coroutines instead of tornado.gen
+ Disable Tornado debug mode by default, add the --debug option
+ Fix node data forwarded to several websockets of a node: the first text
  websocket changed the data seen by the next ones
+ Fix TCP connections left open when a websocket is rejected or closes while
  the connection to the node is being opened
+ Keep forwarding node data to the other websockets when one is closing
+ Do not count a rejected websocket in the per user limit when it closes
+ Time out the connection to a node after 10 seconds
+ Keep UTF-8 characters split across TCP chunks in text mode
+ Do not fail on binary data sent before the node connection is ready
+ Answer 401 or 503 instead of 500 when the API check fails
+ Do not log or echo websocket tokens
+ Remove the unused synchronous API calls

Version 0.4.5
-------------

+ Add the PORT environment variable to the Docker entrypoint
+ Build and push the Docker image from Github Actions

Version 0.4.4
-------------

+ Allow - and _ characters in site names

Version 0.4.3
-------------

+ Fix environment variables passing to the application in Docker

Version 0.4.2
-------------

+ Pass API user credentials via environnement variables in Docker
+ Fix wrong variable name for API port

Version 0.4.1
-------------

+ Add api user/password env variables that were missing in the docker entrypoint

Version 0.4.0
-------------

+ Drop Python 2 support and explicitly support Python 3.6+
+ Use f-string where possible
+ Add Dockerfile

Version 0.3.0
-------------

+ Limit the number of maximum connections per user
+ Handle binary and text streams in separate endpoints
+ Switch CI to Github Actions
+ Add black formatter to lint checks
+ Full test coverage

Version 0.2.0
-------------

+ Fix compatibility issues with Javascript websocket client
+ Improve API class
+ Add tests for API class and logger

Version 0.1.1
-------------

+ Add option --use-local-auth to the service application. This option will
  start the http authentication handler if the authentication host is set to
  localhost

Version 0.1.0
-------------

Initial version
