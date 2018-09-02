# IoT-LAB web_serial_redirection

This application provides a redirection mecanism between the TCP server
connected to the serial port of an IoT-LAB node to websockets clients.

The websocket clients can be started from a web page so this application
allows interacting with the serial port of an IoT-LAB node from a browser.

The application supports Python 2.7 and 3.5 minimum.

## Installation

Install the tornado web framework:

    pip install tornado --pre

## How to use

- Start the application from the command line:

  ```shell
  python application.py --debug --port 8000
  ```

- For a given node, set the key required to access its serial port:

  ```shell
  curl --header "Content-Type: application/json" --request POST --data '{"node":"localhost","key":"key"}' http://localhost:8000/node/key
  ```

- Start the websocket client:

  ```shell
    python websocket_cli.py --host localhost --port 8000 --key key
  ```
