import json

class ServerConfig:
    """ Wonky class to handle json 'database' lol, but it works well as the bot has to interface with
    this infrequently"""
    def __init__(self, path):
        self.path = path
        try:
            with open(path) as f:
                self.conf = json.load(f)
        except:
            self.conf = {}
    def update(self, new_config):
        self.conf = new_config
        with open(self.path, 'w') as f:
            json.dump(self.conf, f)