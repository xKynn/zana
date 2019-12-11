import json
from subprocess import STDOUT, Popen

with open('config.json') as f:
    conf = json.load(f)

if not 'launch' in conf:
    print("Needs 'launch' key in config for process start instructions")
    exit()

while True:
    p = Popen(conf['launch'], shell=True)
    p.wait()
    print("Died")


