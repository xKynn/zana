import json

class ServerConfig:
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