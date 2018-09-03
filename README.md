# IoT-LAB web_serial_redirection

This application provides a redirection mecanism between the TCP server
connected to the serial port of an IoT-LAB node to websockets clients.

The websocket clients can be started from a web page so this application
allows interacting with the serial port of an IoT-LAB node from a browser.

The application supports Python 2.7 and 3.5 minimum.

## Installation

Install using pip:

    pip install . --pre

## How to use

- Start the application from the command line:

  ```shell
  iotlabwebserial-application --debug --port 8000
  ```

- For a given node, set the key required to access its serial port:

  ```shell
  curl --header "Content-Type: application/json" --request POST --data '{"experiment_id":123,"nodes":["localhost"],"key":"key"}' http://localhost:8000/experiment/start
  ```

- Start the websocket client:

  ```shell
  iotlabwebserial- --host localhost --port 8000 --key key
  ```
