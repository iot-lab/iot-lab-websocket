"""Benchmark of websocket connections opened together.

Starts the websocket service and a fake REST API answering after a delay,
then opens websockets all at once and reports the time until they are all
accepted, the failures and the number of API requests.

Usage:

    python benchmarks/handshake.py --api-delay 2 --mode same

--mode same: all the websockets belong to one experiment (one user
opening the nodes of an experiment). --mode distinct: each websocket
belongs to its own experiment. Each round uses new experiment ids, so no
cached API answer is reused from one round to the next.
"""

import argparse
import asyncio
import json
import time

import tornado.web
import tornado.websocket
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_sockets

from iotlabwebsocket.api import ApiClient
from iotlabwebsocket.web_application import WebApplication

TOKEN = "token"
EXPERIMENT_NODES = 200


class FakeApiHandler(tornado.web.RequestHandler):
    # pylint:disable=abstract-method
    """REST API answering the token and node requests after a delay."""

    delay = 0.0
    requests = 0

    async def get(self, _exp_id: str, resource: str) -> None:
        """Answer the token or node list of an experiment."""
        FakeApiHandler.requests += 1
        await asyncio.sleep(FakeApiHandler.delay)
        if resource == "token":
            self.finish(json.dumps({"token": TOKEN}))
            return
        nodes = [
            f"node-{i}.local.iot-lab.info" for i in range(EXPERIMENT_NODES)
        ]
        self.finish(json.dumps({"nodes": nodes}))


def _listen(app: tornado.web.Application) -> int:
    sockets = bind_sockets(0, "127.0.0.1")
    server = HTTPServer(app)
    server.add_sockets(sockets)
    return sockets[0].getsockname()[1]


async def _connect(port: int, exp_id: int, index: int) -> str | None:
    url = f"ws://127.0.0.1:{port}/ws/local/{exp_id}/node-{index}/serial"
    try:
        websocket = await tornado.websocket.websocket_connect(
            url, subprotocols=[f"user{index}", "token", TOKEN]
        )
    except Exception as exc:  # pylint: disable=broad-except
        return str(exc)
    websocket.close()
    return None


async def _round(port: int, count: int, first_exp_id: int, mode: str) -> None:
    FakeApiHandler.requests = 0
    start = time.perf_counter()
    errors = await asyncio.gather(
        *[
            _connect(port, first_exp_id + (i if mode == "distinct" else 0), i)
            for i in range(count)
        ]
    )
    duration = time.perf_counter() - start
    failed = [error for error in errors if error is not None]
    detail = f" ({failed[0]})" if failed else ""
    print(
        f"| {count} | {duration:.2f} s | {len(failed)}{detail} "
        f"| {FakeApiHandler.requests} |"
    )


async def main() -> None:
    """Run the benchmark rounds."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--api-delay",
        type=float,
        default=0.2,
        help="time the fake API takes to answer, in seconds",
    )
    parser.add_argument(
        "--mode",
        choices=["same", "distinct"],
        default="same",
        help="one experiment for all websockets, or one each",
    )
    parser.add_argument(
        "--counts",
        type=int,
        nargs="+",
        default=[10, 20, 40, 80],
        help="numbers of websockets opened together, one round each",
    )
    args = parser.parse_args()

    FakeApiHandler.delay = args.api_delay
    api_port = _listen(
        tornado.web.Application(
            [(r"/api/experiments/(\d+)/(.*)", FakeApiHandler)]
        )
    )
    ws_port = _listen(
        WebApplication(ApiClient("http", "127.0.0.1", str(api_port)))
    )

    print(f"API answering in {args.api_delay} s, mode {args.mode}")
    print("| websockets | all accepted in | failed | API requests |")
    print("|---|---|---|---|")
    for round_index, count in enumerate(args.counts, start=1):
        # Ids spaced so that the experiments of two rounds never overlap
        await _round(ws_port, count, round_index * 10000, args.mode)
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())
