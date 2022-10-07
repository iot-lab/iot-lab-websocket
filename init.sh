#!/bin/bash
set -e

: ${PORT:=8080}
: ${API_PROTOCOL:=http}
: ${API_HOST:=localhost}
: ${API_PORT:=80}
: ${API_USER:=}
: ${API_PASSWORD:=}

export API_USER=${API_USER}
export API_PASSWORD=${API_PASSWORD}

python3 /usr/local/bin/iotlab-websocket-service --port ${PORT} \
    --api-protocol ${API_PROTOCOL} \
    --api-host ${API_HOST} \
    --api-port ${API_PORT} \
    --log-console
