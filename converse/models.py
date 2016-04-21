import datetime
import io

"""
    Base models. Can get backend specific deratives
"""

from .avatar import AvatarFactory

avatarfactory = AvatarFactory()


class Event:
    CONNECT = 0
    DISCONNECT = 1
    CREATE_CHANNEL = 10
    CHANNEL_MESSAGE = 11
    USERJOIN = 12
    USERPART = 13
    NICKCHANGE = 14
    STARTQUERY = 15
    QUERY_MESSAGE = 16

    def __init__(self, type, backend, **details):
        self.type = type
        self.backend = backend
        for (k, v) in details.items():
            setattr(self, k, v)


class Identified:
    _id = 0

    @classmethod
    def generate_id(cls):
        _id = cls._id
        cls._id += 1
        return _id

    def __init__(self):
        self.id = self.generate_id()


class Channel(Identified):
    STATE_PARTED = 0
    STATE_JOINING = 1
    STATE_JOINED = 2
    STATE_KICKED = 3
    STATE_FAILED = 4

    def __init__(self, name, key=""):
        super().__init__()
        self.state = self.STATE_JOINED
        self.name = name
        self.key = key
        self.users = []

    def reset(self):
        """ reset the channel. E.g. after reconnect or kick """
        self.users = []

    def _dump_users(self):
        print("Users on channel {0}: {1}".format(
            self.name,
            ", ".join(str(u) for u in self.users)))

    def add_user(self, user):
        """ will not replace user if present which means you can't update """
        if user not in self.users:
            self.users.append(user)
        self._dump_users()

    def remove_user(self, user):
        try:
            self.users.remove(user)
            return True
        except ValueError:
            return False
        finally:
            self._dump_users()

    def __str__(self):
        return "Channel {0}".format(self.name)


class User(Identified):

    def __init__(self, name):
        super().__init__()
        self.name = name
        self._query = False
        self.avatar = None
        # avatar, id,
        # irc: username, host

    def query(self):
        """ set user in query mode, return True of query
            starts """
        if not self._query:
            self._query = True
            return True
        return False

    def get_avatar(self):
        if self.avatar is None:
            buffer = io.BytesIO()
            avatarfactory.generate(self.name, buffer)
            self.avatar = buffer.getvalue()
        return self.avatar

    def __eq__(self, other):
        try:
            return other and self.name.lower() == other.name.lower()
        except AttributeError:
            return False

    def __str__(self):
        return "{0} ({1})".format(self.name, self.id)


class Message(Identified):

    def __init__(self, user, message):
        super().__init__()
        self.message = message
        self.user = user
        self.timestamp = datetime.datetime.utcnow()


class UserMessage(Message):
    """ message directed at a user """

    def __init__(self, user, message):
        super().__init__(user, message)


class ChannelMessage(Message):
    """ message directed at a channel """

    def __init__(self, user, target, message):
        super().__init__(user, message)
        self.target = target
