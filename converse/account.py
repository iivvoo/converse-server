import random
import sys
import traceback
import datetime
import asyncio
import json

from .models import Event, Identified
from .backend import Backend


class Account(Identified):
    """ too much functionality for just "account". Split into "session"? """

    def __init__(self, username, password, backends):
        super().__init__()
        self.username = username
        self.password = password
        self.backends = backends
        self.connections = []
        self.connection_added = asyncio.Future()

    def save(self):
        return {
            'username': self.username,
            'password': self.password,
            'backends': [
                backend.save() for backend in self.backends
            ]
        }

    def start(self):
        loop = asyncio.get_event_loop()
        for b in self.backends:
            loop.create_task(b.run())
        loop.create_task(self.run())

    def authenticate(self, username, password):
        return self.username == username and self.password == password

    def get_backend_by_id(self, id):
        for be in self.backends:
            if be.id == id:
                return be
        return None

    async def handle(self, message):
        """ handle event coming from client """
        print("Account {0} handle {1}".format(self.username, message))
        try:
            data = json.loads(message)
        except ValueError:
            # should reraise something else so we can send decent error back
            return

        # backend should be part of message? XXX
        backendid = data.get('groupid')
        backend = self.get_backend_by_id(backendid)

        if data['type'] == "GLOBAL_SAVE":
            # let the manager save, which will also eventually
            # invoke self.save(), but for all accounts
            from accountmanager import manager
            manager.save()
        if data['type'] == 'GLOBAL_CONNECT':
            args = data['args']
            await self.add_connection(args)
        if data['type'] == "CHANNEL_MSG":
            await backend.channel_message(data['channelid'],
                                          data['message'])
        if data['type'] == "CHANNEL_JOIN":
            await backend.channel_join(data['name'],
                                       data.get('key'))
        if data['type'] == "CHANNEL_PART":
            await backend.channel_part(data['channelid'])

    def disconnect(self, connection):
        self.connections.remove(connection)

    async def add_connection(self, args):
        type = "irc"
        beklass = Backend.get_backend(type)
        be = beklass("client_created_backend")
        be.setup(args[0], ["#converse"], args[1], int(args[2]),
                 ssl=False)

        self.backends.append(be)
        loop = asyncio.get_event_loop()
        loop.create_task(be.run())

        # notify all connected clients
        for connection in self.connections:
            await self.send_backend_data(connection, be)

    def avatar_url(self, backendid, user):
        return 'http://localhost:8080/avatar/-token-/{0}/{1}/{2}'.format(
            self.id, backendid, user.id
        )
    async def send_backend_data(self, connection, be):
        when = datetime.datetime.utcnow().isoformat() + 'Z'
        msg = json.dumps(
            {"type": "CREATE_GROUP",
             "group": {"id": be.id,
                       "name": be.name},
             "when": when}
        )
        await connection.send(msg)
        for channel in be.channels.values():
            msg = json.dumps(
                {"type": "CREATE_CHANNEL",
                 "groupid": be.id,
                 "channel": {"id": channel.id,
                             "name": channel.name},
                 "when": when}
            )
            await connection.send(msg)
            for user in channel.users:
                msg = json.dumps(
                    {"type": "USERJOIN",
                     "user": {
                         "id": user.id, "name": user.name,
                         "avatar": self.avatar_url(be.id, user)},
                     "groupid": be.id,
                     "channelid": channel.id,
                     "when": when
                     })
                await connection.send(msg)

    async def connect(self, connection):
        self.connections.append(connection)
        self.connection_added.set_result(connection)

        # make connection up to date
        for be in self.backends:
            await self.send_backend_data(connection, be)

    async def handle_event(self, event):
        messages = []

        when = datetime.datetime.utcnow().isoformat() + 'Z'

        if event.type == Event.CONNECT:
            pass
        if event.type == Event.DISCONNECT:
            # notify frontend so channels can be locked/disabled
            pass
        if event.type == Event.CREATE_CHANNEL:
            channel = event.channel
            messages.append({"type": "CREATE_CHANNEL",
                             "groupid": event.backend.id,
                             "channel": {"id": channel.id,
                                         "name": channel.name},
                             "when": when})
        elif event.type == Event.CHANNEL_MESSAGE:
            msg = event.message
            messages.append({"type": "CHANNEL_MESSAGE",
                             "userid": msg.user.id,
                             "groupid": event.backend.id,
                             "channelid": msg.target.id,
                             "message": msg.message,
                             "when": msg.timestamp.isoformat() + 'Z'})
        elif event.type == Event.USERJOIN:
            channel = event.channel
            user = event.user
            messages.append({"type": "USERJOIN",
                             "user": {"id": user.id,
                                      "name": user.name,
                                      "avatar": self.avatar_url(event.backend.id, user)},
                             "groupid": event.backend.id,
                             "channelid": channel.id,
                             "isme": event.isme,
                             "when": when})
        elif event.type == Event.USERPART:
            channel = event.channel
            user = event.user
            messages.append({"type": "USERPART",
                             "userid": user.id,
                             "groupid": event.backend.id,
                             "channelid": channel.id,
                             "isme": event.isme,
                             "when": when})

        elif event.type == Event.NICKCHANGE:
            channel = event.channel
            user = event.user
            messages.append({"type": "NICKCHANGE",
                             "userid": user.id,
                             "groupid": event.backend.id,
                             "channelid": channel.id,
                             "nickname": user.name,
                             "isme": event.isme,
                             "when": when})
        for message in messages:
            up = json.dumps(message)
            print("Sending {0}".format(up))
            # to ALL websockets!
            for connection in self.connections:
                await connection.send(up)

    async def run(self):

        while True:
            try:
                listener_tasks = []
                producer_tasks = []
                closed_tasks = []

                for connection in self.connections:
                    listener_task = asyncio.ensure_future(connection.recv())
                    listener_tasks.append(listener_task)
                    closed_tasks.append(connection.connection_closed)

                for be in self.backends:
                    producer_tasks.append(
                        asyncio.ensure_future(be.queue.get()))

                done, pending = await asyncio.wait(
                    [self.connection_added] +
                    listener_tasks + producer_tasks + closed_tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )

                print("await returned", done)
                if self.connection_added in done:
                    self.connection_added = asyncio.Future()

                for tasks in closed_tasks:
                    if task in done:
                        print("A connection was closed!")
                        print(task.result())

                for task in listener_tasks:
                    if task in done:
                        message = task.result()
                        await self.handle(message)
                    else:
                        task.cancel()

                for task in producer_tasks:
                    if task in done:
                        event = task.result()
                        await self.handle_event(event)
                    else:
                        task.cancel()
            except Exception as e:
                print("Account.run exception", e)
                traceback.print_exc(file=sys.stdout)
