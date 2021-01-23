FROM python:3.8-slim

LABEL maintainer="admin@iot-lab.info"

ARG VERSION=master

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install https://github.com/iot-lab/iot-lab-websocket/archive/$VERSION.tar.gz

COPY init.sh /usr/local/bin/

RUN chmod u+x /usr/local/bin/init.sh
EXPOSE 8080

ENTRYPOINT ["init.sh"]
