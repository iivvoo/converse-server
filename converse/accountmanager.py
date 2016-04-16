import json

from .account import Account
from .backend import Backend


def create_backend(type, name, options):
    klass = Backend.get_backend(type)
    if not klass:
        return  # error

    return klass.create_from_json(name, options)


class AccountManager:

    def __init__(self):
        self.accounts = []

    def get_by_id(self, id):
        for a in self.accounts:
            if a.id == id:
                return a
        return None

    def init(self, file):
        self.file = file

        try:
            with open(file, "r") as f:
                self.config = json.loads(f.read())
        except FileNotFoundError:
            return False

        for a in self.config:
            self.accounts.append(Account(
                username=a['username'],
                password=a['password'],
                backends=[
                    create_backend(b['type'], b['name'], b['options'])
                    for b in a['backends']])
            )
        return True

    def save(self):
        self.config = []
        for a in self.accounts:
            self.config.append(a.save())

        with open(self.file + '.new', "w") as f:
            f.write(json.dumps(self.config, indent=4))

    def startall(self):
        """ start all accounts """
        for a in self.accounts:
            a.start()

manager = AccountManager()
