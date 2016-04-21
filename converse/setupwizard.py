import json

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
