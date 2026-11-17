import copy
import json
import os
import threading
import time

import settings
from net import post_json

LOCK = threading.RLock()
CACHE = {}
CACHE_SECONDS = 8
KEY_PREFIX = "eee2026:"


class StorageError(Exception):
    pass


def remote(*command):
    try:
        reply = post_json(settings.REMOTE_URL, list(command), {"Authorization": "Bearer " + settings.REMOTE_TOKEN}, timeout=10)
    except Exception as problem:
        raise StorageError(f"The online database could not be reached ({problem}).")
    if "error" in reply:
        raise StorageError(f"The online database refused the request ({reply['error']}).")
    return reply.get("result")


def file_path(name):
    return os.path.join(settings.DATA_DIR, name + ".json")


def read(name):
    if not settings.REMOTE_URL:
        if not os.path.exists(file_path(name)):
            return {}
        with open(file_path(name), encoding="utf-8") as f:
            return json.load(f)
    cached = CACHE.get(name)
    if cached and time.time() - cached[0] < CACHE_SECONDS:
        return copy.deepcopy(cached[1])
    try:
        text = remote("GET", KEY_PREFIX + name)
    except StorageError:
        if cached:
            return copy.deepcopy(cached[1])
        raise
    data = json.loads(text) if text else {}
    CACHE[name] = (time.time(), data)
    return copy.deepcopy(data)


def write(name, data):
    if settings.REMOTE_URL:
        remote("SET", KEY_PREFIX + name, json.dumps(data))
        CACHE[name] = (time.time(), copy.deepcopy(data))
        return
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    temporary = file_path(name) + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(temporary, file_path(name))
