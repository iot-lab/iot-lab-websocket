Changelog
=========

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
