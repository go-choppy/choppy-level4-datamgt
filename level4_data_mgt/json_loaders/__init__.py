import os, re, sys

PATTERN = re.compile(r'^[^_][a-zA-Z0-9_\-]+.py$')
LOADERSDIR = os.path.dirname(os.path.abspath(__file__))
LOADERS = [os.path.splitext(loader)[0] for loader in os.listdir(LOADERSDIR) if PATTERN.match(loader)]
sys.path.insert(0, LOADERSDIR)

def load_loader(name):
    if name in LOADERS:
        loader = __import__(name)
        return loader
    else:
        pass

def call_loader(name, json_obj):
    loader = load_loader(name)
    if loader:
        return loader.main(json_obj)
    else:
        return json_obj
