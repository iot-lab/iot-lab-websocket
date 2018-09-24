# IoT-LAB websocket tools

[![Build Status](https://ci.inria.fr/iot-lab/job/iot-lab-websocket/badge/icon)](https://ci.inria.fr/iot-lab/job/iot-lab-websocket/)

This application provides a redirection mecanism between the TCP server
running on an IoT-LAB node to websockets clients.

The websocket clients can be started from a web page thus this application
allows interacting with the serial port of an IoT-LAB node from a browser.

The application supports Python 2.7 and 3.5 minimum.

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
