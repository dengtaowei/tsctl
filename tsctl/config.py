# -*- coding: utf-8 -*-
"""Persistent settings for tsctl."""
from __future__ import print_function

import json
import os

from tsctl import platform as app_platform

DEFAULTS = {
    # Start tsctl when user logs into the desktop
    "app_autostart": False,
    # When tsctl launches, also start Tailscale service
    "start_tailscale_on_launch": False,
}


def config_dir():
    return os.path.join(app_platform.config_home(), "tsctl")


def config_path():
    return os.path.join(config_dir(), "config.json")


def load():
    path = config_path()
    data = dict(DEFAULTS)
    if not os.path.isfile(path):
        return data
    try:
        with open(path, "r") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            for k in DEFAULTS:
                if k in raw:
                    data[k] = bool(raw[k])
    except (IOError, ValueError, TypeError):
        pass
    return data


def save(data):
    path = config_path()
    os.makedirs(config_dir(), exist_ok=True)
    out = dict(DEFAULTS)
    out.update(data)
    # normalize bools
    for k in DEFAULTS:
        out[k] = bool(out.get(k, DEFAULTS[k]))
    with open(path, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    return out
