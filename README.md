# IoT-LAB websocket tools

![CI](https://github.com/iot-lab/iot-lab-websocket/workflows/CI/badge.svg)

This application provides a redirection mecanism between the TCP server
running on an IoT-LAB node to websockets clients.

The websocket clients can be started from a web page thus this application
allows interacting with the serial port of an IoT-LAB node from a browser.

The application supports Python 3.6+.

## Installation

Install using pip:

    pip install . --pre

## How to use

- Start the websocket server from the command line:

  ```shell
  iotlab-websocket-service --use-local-api --token token
  ```

- Start the websocket client:

  ```shell
  iotlab-websocket-client --insecure --api-protocol http  --node localhost.local --exp-id 123
  ```

## Benchmark

`benchmarks/handshake.py` measures how long websockets opened together take
to be accepted, with a fake REST API answering after a given delay:

```shell
python benchmarks/handshake.py --api-delay 2 --mode same
```

`--mode same` opens the websockets for the nodes of one experiment,
`--mode distinct` opens each websocket for its own experiment.
