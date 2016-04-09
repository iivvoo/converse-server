import random
import datetime
import asyncio

from .backend import Backend

from faker import Faker

faker = Faker()

channels = ["#ember", "#python"]

# this backend is currently broken.

def idgenerator():
    i = 0
    while True:
        i += 1
        yield i

newid = idgenerator()


class User:

    def __init__(self, nick, avatar):
        self.id = next(newid)
        self.nick = nick
        self.avatar = avatar

    def dict(self):
        return {'id': self.id,
                'nick': self.nick,
                'avatar': self.avatar}

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id


class Channel:

    def __init__(self, name):
        self.name = name
        self.users = []

    def generate_event(self):
        """ generate some random event """
        r = random.choice(range(10))
        now = datetime.datetime.utcnow().isoformat() + 'Z'

        if r == 0 or len(self.users) == 0:
            remain = set(users) - set(self.users)
            if len(remain) > 0:
                newuser = random.choice(list(remain))
                self.users.append(newuser)
                return dict(action="JOIN",
                            channel=self.name,
                            when=now,
                            user=newuser.dict())
        elif r == 1:
            if len(self.users) > 0:
                remove = random.choice(self.users)
                self.users.remove(remove)
                return dict(action="PART",
                            channel=self.name,
                            when=now,
                            user=remove.dict())

        u = random.choice(self.users)
        return dict(action="MSG",
                    when=now,
                    channel=self.name,
                    user=u.dict(),
                    message=faker.text())

users = [
    User("iivvoo",
         "avatar-url"),
    User("vladdrac",
         "avatar-url"),
    User("torvalds",
         "avatar-url"),
    User("vladbot", "avatar-url"),
    User("nick123", "avatar-url"),
    User("test", "avatar-url"),
    User("gvr", "avatar-url"),
]

channellist = {c: Channel(c) for c in channels}


def generate_update():
    c = random.choice(list(channellist.values()))
    return c.generate_event()


class RandomBackend(Backend):

    def __init__(self, name):
        super().__init__()
        self.name = name

    async def run(self):
        for i in range(0, 100):
            print ("Putting something")
            await self.queue.put(generate_update())

        while True:
            print ("Generating something")
            await qself.ueue.put(generate_update())
            await asyncio.sleep(random.random() * 3)
