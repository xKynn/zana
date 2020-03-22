import json
from subprocess import Popen

with open('config.json') as file:
    config = json.load(file)

launch = config.get('launch')
if not launch:
    print("Needs 'launch' key in config for process start instructions")
    exit()

while True:
    p = Popen(launch, shell=True)
    p.wait()
    print('Process died')
