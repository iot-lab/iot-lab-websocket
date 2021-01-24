#!/bin/bash
set -e

: ${API_PROTOCOL:=http}
: ${API_HOST:=localhost}
: ${API_PORT:=80}
: ${API_USER:=}
: ${API_PASSWORD:=}

python3 /usr/local/bin/iotlab-websocket-service --port 8080 \
    --api-protocol ${API_PROTOCOL} \
    --api-host ${API_HOST} \
    --api-port ${API_HOST} \
    --api-user ${API_USER} \
    --api-password ${API_PASSWORD} \
    --log-console
