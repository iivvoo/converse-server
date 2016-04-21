#!/usr/bin/env python

import sys
import datetime
import random
import logging
from urllib.parse import urlparse, parse_qsl

import asyncio
import websockets

from .ircbackend import IRCBackend
from .account import Account

from .randombackend import RandomBackend
from .accountmanager import manager
from .setupwizard import initial_setup
from .webserver import ConverseWebServer

log = logging.getLogger('bottom')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


wslog = logging.getLogger('websockets')
wslog.setLevel(logging.INFO)
wslog.addHandler(logging.StreamHandler())

logging.basicConfig(level=logging.DEBUG)


async def server(websocket, path):  # noqa

    account = None
    print(websocket)
    while account is None:

        message = await websocket.recv()
        print("Waiting for auth, received {0}".format(message))
        try:
            username, password = message.strip().split(None, 1)
        except ValueError:
            username = message.strip()
            password = username

        for a in manager.accounts:
            if a.authenticate(username, password):
                account = a
                await a.connect(websocket)
                print("Auth {0} success".format(username))
                await websocket.send("CONVERSE AUTH 1001 :Welcome\n")
                break
        else:
            await websocket.send("CONVERSE AUTH 1002 :Invalid credentials\n")

    done, pending = await asyncio.wait([websocket.connection_closed],
                                       return_when=asyncio.FIRST_COMPLETED)
    print("Connection was closed")
    account.disconnect(websocket)


def main():
    loop = asyncio.get_event_loop()

    start_server = websockets.serve(server, '127.0.0.1', 5678)
    print(start_server)

    if not manager.init('config.json'):
        initial_setup()
        sys.exit(0)

    manager.startall()

    loop.set_debug(True)
    loop.run_until_complete(start_server)
    f = loop.create_server(
        lambda: ConverseWebServer(debug=True, keep_alive=75),
        '0.0.0.0', '8080')

    srv = loop.run_until_complete(f)
    loop.run_forever()
