import sys
import random
import asyncio
import bottom

from faker import Faker

faker = Faker()

# host = 'chat.freenode.net'
# port = 6697
# ssl = True
host = 'localhost'
port = 6667
ssl = False


class Bot:

    def __init__(self, nick, channels, noiselevel=5):
        self.nick = nick
        self.channels = channels
        self.noiselevel = noiselevel
        self.client = bottom.Client(host=host, port=port, ssl=ssl)

        self.client.on('CLIENT_CONNECT', self.handle_connect)
        self.client.on('PING', self.keepalive)
        self.client.on('PRIVMSG', self.message)
        self.client.on('RPL_WELCOME', self.loop)
        self.silence = False

    async def run(self):
        await self.client.connect()

    def handle_connect(self, **kwargs):
        self.client.send('NICK', nick=self.nick)
        self.client.send('USER', user=self.nick,
                         realname='Ivo van der Wijk')
        for channel in self.channels:
            self.client.send('JOIN', channel=channel)

    def keepalive(self, message, **kwargs):
        self.client.send('PONG', message=message)

    def message(self, nick, target, message, **kwargs):
        """ Echo all messages """

        # Don't echo ourselves
        if nick == self.nick:
            return
        # Respond directly to direct messages
        if target == self.nick:
            self.client.send("PRIVMSG", target=nick, message=message)
        # Channel message
        elif message.lower().startswith(self.nick.lower()):
            self.client.send("PRIVMSG", target=target,
                             message=message.split(" ", 1)[-1])
        elif message.lower().startswith("silence"):
            self.client.send("PRIVMSG", target=target, message="Shhhht!")
            self.silence = not self.silence

    async def loop(self, *args, **kwrags):
        while True:
            await asyncio.sleep(random.random() *
                                (10 * (self.noiselevel + 10)))
            if self.silence:
                continue

            print ("Generating something")
            dice = random.choice(range(50))
            if dice == 1:
                c = random.choice(self.channels)
                self.client.send("PART", channel=c)
                await asyncio.sleep(20)
                self.client.send("JOIN", channel=c)
            elif 1 < dice < 8:
                self.client.send("NICK", nick=faker.first_name())
            else:
                for i in range(random.choice((1, 1, 1, 2, 2, 3, 4))):
                    self.client.send("PRIVMSG",
                                     target=random.choice(self.channels),
                                     message=faker.text())


def main():
    channels = ["#converse"]
    botcount = 40

    if len(sys.argv) > 1:
        botcount = int(sys.argv[1])

    loop = asyncio.get_event_loop()
    async def startbots():
        for i in range(botcount):
            b = Bot(faker.first_name(), channels, random.choice(range(10)))
            print("{0} created".format(b.nick))
            loop.create_task(b.run())
            await asyncio.sleep(random.random() * 2)

    loop.create_task(startbots())
    loop.run_forever()
