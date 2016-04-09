import bottom
import datetime
import asyncio

from .backend import Backend
from .models import Event, Channel, User, ChannelMessage, UserMessage


def parse_prefixnick(prefixnick):
    possible_prefix = prefixnick[0]
    if possible_prefix in "+@":
        return possible_prefix, prefixnick[1:]
    return "", prefixnick


class IRCBackend(Backend):
    type = "irc"
    """
        It would be nice if we could somehow confirm our nickname back
        from the server. It's in each reply but 'bottom' filters it from
        the events
    """

    def setup(self, nick, channels, host, port=6667,
              ssl=True, **rest):
        self.nick = nick
        self.autojoin_channels = channels
        self.ircserver = host
        self.ircport = port
        self.ssl = ssl
        self.realname = "Hey there"
        self.client = None

        self.firstconnect = False

        # local bookkeeping. Assumed to be generic -> Backend?
        self.users = {}  # ordered dict to preserve irc order?
        self.channels = {}

    def save(self):
        data = super().save()
        data['options'].update({
            "nick": self.nick,
            "host": self.ircserver,
            "port": self.ircport,
            "ssl": self.ssl,
            "channels": [
                c.name for c in self.channels.values()
            ]
        })
        return data

    def isme(self, nick):
        return nick.lower() == self.nick.lower()

    async def run(self):
        self.client = bottom.Client(host=self.ircserver, port=self.ircport,
                                    ssl=self.ssl)

        self.client.on('CLIENT_CONNECT', self.handle_connect)
        self.client.on('CLIENT_DISCONNECT', self.handle_disconnect)
        self.client.on('RPL_WELCOME', self.handle_welcome)
        self.client.on('RPL_MYINFO', self.handle_myinfo)
        self.client.on('PING', self.handle_ping)
        self.client.on('PRIVMSG', self.handle_privmsg)
        self.client.on('JOIN', self.handle_join)
        self.client.on('PART', self.handle_part)
        self.client.on('KICK', self.handle_kick)
        self.client.on('QUIT', self.handle_quit)
        self.client.on('NICK', self.handle_nick)
        self.client.on('RPL_NAMREPLY', self.handle_namreply)
        await self.client.connect()

    async def handle_connect(self, **kwargs):
        print("CONNECT", kwargs)
        await self.enqueue(Event.CONNECT)
        self.client.send('NICK', nick=self.nick)
        self.client.send('USER', user=self.nick,
                         realname=self.realname)

        # The first connection will join the configured channels,
        # later connections (e.g. after disconnect+reconnect) will
        # join active channels

        if not self.firstconnect:
            self.firstconnect = True
            for channel in self.autojoin_channels:
                self.client.send('JOIN', channel=channel)
        else:
            for channel in self.channels.values():
                channel.reset()
                self.client.send('JOIN', channel=channel.name, key=channel.key)

    def reset(self):
        """ reset state. E.g. after disconnect """
        self.users = {}

    async def handle_disconnect(self, **kwargs):
        print("Disconnect")
        self.reset()
        await self.enqueue(Event.DISCONNECT)
        await asyncio.sleep(3)
        print("Attempt reconnect")
        await self.client.connect()

        await self.client.wait("client_connect")
        print("Connected again!")

    async def handle_nick(self, nick, user, newnick, host, **args):
        isme = self.isme(nick)
        if isme:
            self.nick = newnick

        user = self.get_create_user(nick)
        self.change_nick(user, newnick)
        for channel in self.channels.values():
            if user not in channel.users:
                continue

            await self.enqueue(Event.NICKCHANGE, channel=channel,
                               user=user, isme=isme)

    async def handle_namreply(self, channel, names, **kwargs):
        channel = self.get_create_channel(channel)
        for name in names:
            # a name is a nick, optionally prefixed with '+' or '@'.
            # available prefixes may have been repored through a 005
            # reply when connecting
            prefix, nick = parse_prefixnick(name)
            # define a IRCUser that knows about op-ed and voiced users
            user = self.get_create_user(nick)
            channel.add_user(user)
            await self.enqueue(Event.USERJOIN, channel=channel, user=user,
                               isme=self.isme(nick))

    async def enqueue(self, type, **args):
        await self.queue.put(Event(type, self, **args))

    async def handle_part(self, nick, user, channel, host, **kwargs):
        # XXX Was it me? -> update channel state
        user = self.get_create_user(nick)
        channel = self.get_create_channel(channel)
        channel.remove_user(user)
        await self.enqueue(Event.USERPART, isme=self.isme(nick),
                           channel=channel, user=user)

    async def handle_kick(self, nick, user, channel, target, host, message,
                          **kwargs):
        # XXX Was it me? -> update channel state
        user = self.get_create_user(nick)
        channel = self.get_create_channel(channel)
        channel.remove_user(user)
        await self.enqueue(Event.USERPART, isme=self.isme(nick),
                           channel=channel, user=user)

    async def handle_quit(self, nick, host, user, message, **kwargs):
        """ A quit is not related to a specific channel, it can apply
            to all """
        user = self.get_create_user(nick)
        for channel in self.channels.values():
            if channel.remove_user(user):
                await self.enqueue(Event.USERPART, channel=channel, user=user,
                                   isme=self.isme(nick))

    def handle_welcome(self, **kwargs):
        print("WELCOME", kwargs)

    def handle_myinfo(self, **kwargs):
        print("MYINFO", kwargs)

    def handle_ping(self, message, **kwargs):
        self.client.send('PONG', message=message)

    async def handle_join(self, nick, user, channel, **kwargs):
        print("JOIN {0} {1} {2} {3}".format(nick, user, channel, kwargs))
        channel = self.get_create_channel(channel)
        user = self.get_create_user(nick)

        if self.isme(nick):
            print("JOIN it appears I joined {0}".format(channel))
            await self.enqueue(Event.CREATE_CHANNEL, channel=channel)

        channel.add_user(user)
        await self.enqueue(Event.USERJOIN, channel=channel, user=user,
                           isme=self.isme(nick))

    def change_nick(self, user, newnick):
        """ update the local user registry and the user itself """
        self.users.pop(user.name.lower())
        user.name = newnick
        self.users[user.name.lower()] = user

    def get_create_user(self, name):
        """
            'name' (nick) can change which means updating
            the dictionary. We may need to consider indexing
            by id in stead?
        """
        u = self.users.get(name.lower())

        if u is None:
            u = User(name)
            self.users[name.lower()] = u
        return u

    def get_user_by_id(self, id):
        for u in self.users.values():
            if u.id == id:
                return u
        return None

    def get_create_channel(self, name):
        c = self.channels.get(name.lower())

        if c is None:
            c = Channel(name)
            self.channels[name.lower()] = c
        return c

    async def handle_privmsg(self, nick, target, message, **kwargs):
        print("PRIVMSG", nick, target, message)

        user = self.get_create_user(nick)
        channel = self.get_create_channel(target)  # can also be user!

        channel._dump_users()
        print(str(user))
        await self.enqueue(Event.CHANNEL_MESSAGE,
                           message=ChannelMessage(
                               message=message,
                               target=channel,
                               user=user
                           ))
    # client commands

    def find_channel_by_id(self, channelid):
        for c in self.channels.values():
            if c.id == channelid:
                return c
        return None

    async def channel_message(self, channelid, message):
        """ Handle message send by the client """
        channel = self.find_channel_by_id(channelid)
        user = self.get_create_user(self.nick)

        if not (channel and user):
            return

        self.client.send('PRIVMSG',
                         target=channel.name,
                         message=message)
        await self.enqueue(Event.CHANNEL_MESSAGE,
                           message=ChannelMessage(
                               message=message,
                               target=channel,
                               user=user
                           ))

    async def channel_join(self, name, key=None):
        """ handle client JOIN command """
        self.client.send('JOIN', channel=name, key=key)

    async def channel_part(self, channelid, key=None):
        """ handle clent PART command """
        channel = self.find_channel_by_id(channelid)
        if channel:
            self.client.send('PART', channel=channel.name)

Backend.register(IRCBackend)
