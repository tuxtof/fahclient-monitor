#!/usr/bin/env python3

import os
import sys
import time
import datetime
import asyncio
from influxdb import InfluxDBClient
import logging

# Settings


influxServer = os.getenv("INFLUX_HOST", "influx")
influxPort = os.getenv("INFLUX_PORT", 443)
influxUser = os.getenv("INFLUX_USER", "fahclient")
influxPassword = os.getenv("INFLUX_PASSWORD")
influxDatabase = os.getenv("INFLUX_DB", "fahclient")

fahclientID = os.getenv("ID", "fahclient")
fahclientServer = os.getenv("FAHCLIENT_HOST", "localhost")
fahclientPort = os.getenv("FAHCLIENT_PORT", 36330)

logLevel = os.getenv("LOG", "WARNING")
interval = int(os.getenv("INTERVAL", 5))

# Configure Log system

numeric_level = getattr(logging, logLevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % logLevel)
logging.basicConfig(
    format='%(asctime)s :: %(levelname)s :: %(message)s', level=numeric_level)


# Init InfluxDB Client

db = InfluxDBClient(influxServer, influxPort, influxUser,
                    influxPassword, influxDatabase, True, True)


def get_eta(data):
    time_patterns = ["%M mins %S secs", "%H hours %M mins", "%S.00 secs"]

    for pattern in time_patterns:
        try:
            pt = datetime.datetime.strptime(data, pattern)
            return pt.second + pt.minute*60 + pt.hour*3600
        except:
            pass

    logging.error("ETA is not in expected format: %s" % data)
    sys.exit(0)


def fahclient_event_parse(data):
    logging.debug('Data received: {!r}'.format(data.decode()))
    msg = data.decode()
    posStart = msg.find("\nPyON 1 units")
    posEnd = msg.find("\n---\n")

    if posStart >= 0 and posEnd >= 0:

        msgContent = msg[posStart+14:posEnd+1]

        msgDecoded = eval(msgContent, {}, {})
        logging.debug(msgDecoded)
        fahclient_event_send(msgDecoded)


def fahclient_event_send(data):

    for queue in data:
        json_body = [
            {
                "measurement": "queue_info",
                "tags": {
                    "host": fahclientID,
                    "project": queue["project"],
                    "core": queue["core"],
                    "state": queue["state"]
                },
                "fields": {
                    "percentdone": float(queue["percentdone"][:-1]),
                    "ppd": int(queue["ppd"]),
                    "creditestimate": int(queue["creditestimate"]),
                    "eta": get_eta(queue["eta"])
                }
            }
        ]

        logging.debug(json_body)
        db.write_points(json_body)

# Init FAHClient class


class FAHClientProtocol(asyncio.Protocol):
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost

    def connection_made(self, transport):
        transport.write(self.message.encode())
        logging.info('Connection opened')

    def data_received(self, data):
        fahclient_event_parse(data)

    def connection_lost(self, exc):
        logging.info('The server closed the connection')
        self.on_con_lost.set_result(True)


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = 'updates add 0 %s $queue-info\r\n' % interval

    transport, protocol = await loop.create_connection(
        lambda: FAHClientProtocol(message, on_con_lost),
        fahclientServer, fahclientPort)

    # Wait until the protocol signals that the connection
    # is lost and close the transport.
    try:
        await on_con_lost
    finally:
        transport.close()


asyncio.run(main())
