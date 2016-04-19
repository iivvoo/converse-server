#!/usr/bin/env python

import json
import sys
import datetime
import random
import logging
from urllib.parse import urlparse, parse_qsl

import asyncio
import websockets

import aiohttp
import aiohttp.server

from .ircbackend import IRCBackend
from .account import Account

from .randombackend import RandomBackend


from .accountmanager import manager

log = logging.getLogger('bottom')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


wslog = logging.getLogger('websockets')
wslog.setLevel(logging.INFO)
wslog.addHandler(logging.StreamHandler())

logging.basicConfig(level=logging.DEBUG)


class ConverseWebServer(aiohttp.server.ServerHttpProtocol):
    async def handle_request(self, message, payload):
        # /avatar/token/<acctid>/<backendid>/<userid>
        parts = message.path.split('/')
        status_code = 404
        ct = "text/html"
        msg = b"<h1>Not found</h1>"

        if len(parts) == 6:  # ('', 'avatar', 'token', id, id, id)
            _, ns, token, acctid, backendid, userid = parts
            if ns == 'avatar':
                account = manager.get_by_id(int(acctid))
                be = account.get_backend_by_id(int(backendid))
                user = be.get_user_by_id(int(userid))
                msg = user.get_avatar()
                status_code = 200
                ct = "image/png"

        response = aiohttp.Response(
            self.writer, status_code, http_version=message.version
        )
        response.add_header('Content-Type', ct)
        response.add_header('Content-Length', str(len(msg)))
        response.send_headers()
        response.write(msg)
        await response.write_eof()

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


def initial_setup():
    """ called when no initial config present, creates minimal config """
    print("You don't seem to have a config.json. Let's create one, ")
    input("Hit entry to continue, ^C to cancel")
    print("Enter a username for the account")
    username = input("username: ")
    print("Enter a password for the account")
    password = input("password: ")
    print()
    print("I'll assume you want to setup an irc backend. Enter the host name "
          "followed (optionally) by a port number")
    irchostport = input("Enter server details, e.g. localhost 6667> ")
    parts = irchostport.split()
    host = parts[0]
    port = 6667
    if len(parts) > 1:
        port = int(parts[1])

    print()
    print("Enter the nickname you want to use")
    nick = input("nick> ")
    print("Enter a channel you want to join. Separate multiple channels using "
          "comma's")
    channels = input("channel(s)> ")
    channels = channels.split(",")

    config = [{"username": username, "password": password, "backends": [
        {"type": "irc",
         "name": "{0}@irc".format(username),
         "options": {
             "channels": channels,
             "nick": nick,
             "host": host,
             "port": port,
             "ssl": False
             }
         }
    ]}]
    config = json.dumps(config, indent=4)
    print("Here's your config:")
    print(config)
    print("I wrote it to config.json. I hope it works for you")
    with open("config.json", "w") as o:
        o.write(config)
        

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
