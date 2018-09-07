# IoT-LAB websocket tools

This application provides a redirection mecanism between the TCP server
connected to the serial port of an IoT-LAB node to websockets clients.

The websocket clients can be started from a web page so this application
allows interacting with the serial port of an IoT-LAB node from a browser.

The application supports Python 2.7 and 3.5 minimum.

## Installation

Install using pip:

    pip install . --pre

## How to use

- Start the websocket application from the command line:

  ```shell
  iotlab-websocket-service --debug --port 8000
  ```

- Start the websocket client:

  ```shell
  iotlab-websocket-client --host localhost --port 8000 --token token --id 123
  ```
