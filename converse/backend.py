import asyncio

from .models import Identified


class Backend(Identified):
    _reg = {}

    type = 'base'

    @classmethod
    def register(cls, backend):
        cls._reg[backend.type] = backend

    @classmethod
    def get_backend(cls, backendid):
        return cls._reg.get(backendid)

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.queue = asyncio.Queue()

    def setup(self, **options):
        for (k, v) in options.items():
            setattr(self, k, v)

    @classmethod
    def create_from_json(cls, name, options):
        i = cls(name)
        i.setup(**options)
        return i

    def save(self):
        """ return json-serializable data for saving """
        return {'name': self.name,
                'type': self.type,
                'options': {}}

    async def run(self):
        pass

    def channel_message(self, channelid, message):
        pass

    def channel_join(self, name, key=None):
        pass

    def channel_part(self, channelid):
        pass
