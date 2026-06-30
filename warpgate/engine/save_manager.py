import json
import os

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")
NUM_SLOTS = 3

def _path(slot):
    os.makedirs(SAVE_DIR, exist_ok=True)
    return os.path.join(SAVE_DIR, f"save_{slot}.json")

def save(slot, data):
    with open(_path(slot), "w") as f:
        json.dump(data, f, indent=2)

def load(slot):
    p = _path(slot)
    if not os.path.exists(p):
        return None
    with open(p, "r") as f:
        return json.load(f)

def slot_info(slot):
    data = load(slot)
    if data is None:
        return None
    return {
        "location": data.get("location", "UNKNOWN"),
        "playtime": data.get("playtime", 0),
        "corruption": data.get("corruption", 0),
        "party": data.get("party_summary", []),
    }

def delete(slot):
    p = _path(slot)
    if os.path.exists(p):
        os.remove(p)
