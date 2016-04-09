# Converse Server

Converse Server is the server/proxy component for the multi protocol Converse client.

## Installation

Converse isn't ready yet for end users yet so if you install it I assume you will probably want to tweak it and at least have some python knowledge.

If you're crazy enough to give this a try, find me (iivvoo) on freenode if you need any help

Converse requires python3.5 (it uses the async/await syntax so 3.4 really won't work). On ubuntu 14.04 you can use the deadsnakes repository to get this version:

https://launchpad.net/~fkrull/+archive/ubuntu/deadsnakes

Coverse requires (and installs) Pillow for generating avatars and will need
libfreetype6-dev (on Ubuntu) to be installed first

It's probably the safest to install in a virtualenv.

    $ virtualenv -p /usr/bin/python3.5 converse

And then install converse

    $ converse/bin/pip install -e git+git://github.com/iivvoo/converse-server.git#egg=converse-server

Converse depends on a forked version of bottom (https://github.com/numberoverzero/bottomhttps://github.com/numberoverzero/bottom)
which can't be easiliy installed from a setuptools setup.py so install it
separately for now

    $ converse/bin/pip install -e git+git://github.com/iivvoo/bottom.git#egg=bottom

(it will eventually, hopefully, be merged back with the main bottom repo)

## Starting converse

It's best to test against a local irc daemon first. Converse needs
a config file (config.json) that looks as follows:

    [
        {
            "username": "demo",
            "backends": [
                {
                    "type": "irc",
                    "name": "converse@localirc",
                    "options": {
                        "channels": [
                            "#converse"
                        ],
                        "nick": "Converser",
                        "host": "localhost",
                        "port": 6667,
                        "ssl": false
                    }
                }
            ],
            "password": "demo"
        }
    ]
