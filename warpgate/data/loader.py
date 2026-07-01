import json
import os

_CACHE = {}

def _path(filename):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, "assets", "data", filename)

def load(filename):
    if filename not in _CACHE:
        with open(_path(filename), "r") as f:
            _CACHE[filename] = json.load(f)
    return _CACHE[filename]

def enemies():
    return load("config/enemies.json")

def items():
    return load("config/items.json")

def spells():
    return load("config/spells.json")

def story():
    return load("config/story.json")
